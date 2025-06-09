#!/usr/bin/env python3
"""
Download module for downloading videos from Xiaohongshu
"""
import os
import re
import time
import json
import logging
import requests
import random
from urllib.parse import urlparse
from .utils import clean_url, setup_logging, find_video_urls_in_text, find_video_urls_in_json

def resolve_short_url(short_url):
    """Resolve a short URL to get the final destination URL"""
    try:
        logging.debug(f"Resolving short URL: {short_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Referer': 'https://www.xiaohongshu.com/',
            'Cookie': 'xhsTrackerId=cebd0c81-0c81-0c81-0c81-0c810c810c81; xhsuid=0c810c810c810c81; timestamp2=0c810c810c810c81; timestamp2.sig=0c810c810c810c81'
        }
        
        # Add a random delay to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        response = requests.head(short_url, headers=headers, allow_redirects=True, timeout=30)
        logging.debug(f"Short URL resolved to: {response.url}")
        return response.url
    except requests.RequestException as e:
        logging.error(f"Failed to resolve short URL: {e}")
        return None

def extract_json_blocks(html_content):
    """Extract all potential JSON blocks from the HTML content"""
    json_blocks = []
    
    # Try to find JSON blocks with various patterns
    patterns = [
        r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>',
        r'<script>window\.__REDUX_STATE__\s*=\s*({.*?});</script>',
        r'"video"\s*:\s*({.*?}),\s*"image"',
        r'"stream"\s*:\s*({.*?})\s*}',
        r'{"h265":(\[.*?\]),"h266"',
        r'{"h264":(\[.*?\]),"h265"',
        r'{"stream":({.*?}),"image"',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, html_content, re.DOTALL)
        for match in matches:
            json_blocks.append(match.group(1))
    
    return json_blocks

def is_valid_caption(caption):
    """
    Check if the caption is valid and not a default/invalid value
    """
    if not caption:
        return False
        
    # List of invalid/default captions to filter out
    invalid_captions = [
        'xhs_www.xiaohongshu.com',
        'hs_www.xiaohongshu.com',
        'www.xiaohongshu.com',
        'xiaohongshu.com',
        'xhs_video_',
        'xhs_'
    ]
    
    # Check if caption matches any invalid pattern
    for invalid in invalid_captions:
        if invalid in caption:
            return False
    
    # Check if caption is too short or just numbers
    if len(caption) < 2 or caption.isdigit():
        return False
        
    return True

def extract_video_caption(html_content):
    """Extract video caption/title and hashtags from HTML"""
    caption = None
    hashtags = []
    
    # First try to get title from detail-title
    title_pattern = r'<div id="detail-title" class="title"[^>]*>(.*?)</div>'
    title_match = re.search(title_pattern, html_content, re.DOTALL)
    if title_match:
        caption = title_match.group(1).strip()
        if not is_valid_caption(caption):
            caption = None
    
    # If no valid title found, try to get caption from detail-desc
    if not caption:
        desc_pattern = r'<div id="detail-desc" class="desc"[^>]*>.*?<span class="note-text"[^>]*>.*?<span[^>]*>(.*?)</span>'
        desc_match = re.search(desc_pattern, html_content, re.DOTALL)
        if desc_match:
            caption = desc_match.group(1).strip()
            if not is_valid_caption(caption):
                caption = None
    
    # Extract hashtags from tag links
    hashtag_pattern = r'<a[^>]*class="tag"[^>]*>#([^<]+)</a>'
    hashtag_matches = re.finditer(hashtag_pattern, html_content)
    for match in hashtag_matches:
        hashtag = match.group(1).strip()
        if hashtag:
            hashtags.append(f"#{hashtag}")
    
    # If we have a valid caption or hashtags, combine them
    if is_valid_caption(caption) or hashtags:
        # Clean up caption
        if caption:
            # Remove any existing hashtags from caption
            caption = re.sub(r'#\w+\s*', '', caption).strip()
            # Remove any special characters that might cause issues
            caption = re.sub(r'[\\/*?:"<>|]', '', caption)
            # Replace multiple spaces with single space
            caption = re.sub(r'\s+', ' ', caption).strip()
        
        # Combine caption and hashtags
        if caption and hashtags:
            final_caption = f"{caption} {' '.join(hashtags)}"
        elif caption:
            final_caption = caption
        else:
            final_caption = ' '.join(hashtags)
        
        logging.debug(f"Found caption: {final_caption}")
        return final_caption
    
    return None

def extract_video_data(page_url):
    """Extract video URLs from a Xiaohongshu page"""
    logging.info(f"Extracting video data from: {page_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://www.xiaohongshu.com/',
        'Cookie': 'xhsTrackerId=cebd0c81-0c81-0c81-0c81-0c810c810c81; xhsuid=0c810c810c810c81; timestamp2=0c810c810c810c81; timestamp2.sig=0c810c810c810c81'
    }
    
    try:
        # Add a random delay to mimic human behavior
        time.sleep(random.uniform(2, 5))
        
        response = requests.get(page_url, headers=headers, timeout=30)
        logging.debug(f"Status code: {response.status_code}")
        
        # First, try direct regex extraction from raw HTML
        video_urls = find_video_urls_in_text(response.text)
        
        # Extract all potential JSON blocks
        json_blocks = extract_json_blocks(response.text)
        logging.debug(f"Found {len(json_blocks)} potential JSON blocks")
        
        all_video_urls = set(video_urls)
        
        # Try to parse each JSON block
        for i, block in enumerate(json_blocks):
            try:
                # Clean up the JSON string
                block = block.replace('\\"', '"').replace("\\'", "'")
                json_data = json.loads(block)
                
                # Find videos in this JSON block
                found_urls = find_video_urls_in_json(json_data)
                all_video_urls.update(found_urls)
            except json.JSONDecodeError:
                continue
        
        # Try to find stream data specifically in the HTML content
        stream_patterns = [
            r'"stream"\s*:\s*({.*?}),\s*"image"',
            r'"h265"\s*:\s*(\[.*?\]),\s*"h266"',
            r'"h264"\s*:\s*(\[.*?\])'
        ]
        
        for pattern in stream_patterns:
            matches = re.search(pattern, response.text, re.DOTALL)
            if matches:
                try:
                    stream_data = matches.group(1)
                    clean_data = stream_data.replace('\\"', '"').replace("\\'", "'").replace('\\u002F', '/')
                    
                    # Try to extract video URLs directly from this data
                    more_urls = find_video_urls_in_text(clean_data)
                    all_video_urls.update(more_urls)
                except Exception:
                    continue
        
        # Try to extract video caption/title for filename
        caption = extract_video_caption(response.text)
        
        return list(all_video_urls), caption
        
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None, None

def download_video(url, filename=None, output_dir='downloads'):
    """Download a video file from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.xiaohongshu.com/'
        }
        
        # Create downloads directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            filename = path_parts[-1]
        
        # Add file extension if missing
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        # Make sure filename is valid
        filename = re.sub(r'[\\/*?:"<>|]', '', filename)  # Remove invalid characters
        
        filepath = os.path.join(output_dir, filename)
        
        # Download with progress reporting
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            logging.info(f"Downloading: {filename}")
            logging.info(f"Size: {total_size / (1024 * 1024):.2f} MB")
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int(50 * downloaded / total_size)
                            progress_bar = f"[{'=' * progress}{' ' * (50 - progress)}] {downloaded / total_size:.1%}"
                            logging.debug(progress_bar)
            
            logging.info(f"Download complete: {filepath}")
            return filepath
            
    except Exception as e:
        logging.error(f"Download failed: {e}")
        return None

def download_video_from_url(url, output_dir='downloads', debug=False):
    """Process a URL to extract and download video"""
    # Setup logging
    setup_logging(debug)
    
    # Resolve short URL if needed
    if 'xhslink.com' in url or 't.cn' in url:
        logging.info(f"Resolving short URL: {url}")
        resolved_url = resolve_short_url(url)
        if not resolved_url:
            logging.error("Failed to resolve short URL")
            return None
        url = resolved_url
        logging.info(f"Resolved to: {url}")
    
    # Extract video data
    video_urls, caption = extract_video_data(url)
    
    if not video_urls or len(video_urls) == 0:
        logging.error("Failed to find any video URLs")
        return None
    
    logging.info(f"Found {len(video_urls)} video URLs")
    
    # Use the first video URL (highest quality usually)
    selected_url = video_urls[0]
    
    # Generate filename
    if caption and is_valid_caption(caption):
        # Use first 50 chars of caption for filename
        filename = caption[:50]
    else:
        # Extract video ID from URL
        match = re.search(r'/([^/]+)', url)
        if match:
            video_id = match.group(1)
            if is_valid_caption(video_id):
                filename = f"xhs_{video_id}"
            else:
                filename = f"xhs_video_{int(time.time())}"
        else:
            filename = f"xhs_video_{int(time.time())}"
    
    # Download the video
    return download_video(selected_url, filename, output_dir)