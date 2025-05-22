#!/usr/bin/env python3
"""
Utility functions for the downloader module
"""
import re
import logging

def setup_logging(debug=False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def clean_url(url):
    """Clean up URLs by replacing escape sequences"""
    if not url:
        return ""
    # Replace unicode escape sequences
    url = url.replace(r'\u002F', '/').replace('\\/', '/')
    # Remove any double slashes (except for http://)
    url = re.sub(r'(?<!:)\/\/', '/', url)
    return url

def find_video_urls_in_text(text):
    """Extract video URLs using regex patterns"""
    # Create patterns to find video URLs
    video_patterns = [
        r'(https?://[^"\s]+\.xhscdn\.com/stream/[^"\s]+\.mp4)',
        r'(http:\\u002F\\u002F[^"\\]+\.xhscdn\.com\\u002Fstream\\u002F[^"\\]+\.mp4)',
        r'"masterUrl"\s*:\s*"([^"]+\.mp4)"',
        r'"backupUrls"\s*:\s*\[\s*"([^"]+)"'
    ]
    
    video_urls = set()
    for pattern in video_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean = clean_url(match)
            if clean:
                video_urls.add(clean)
    
    return list(video_urls)

def find_video_urls_in_json(json_data):
    """Search through JSON structure for video URLs"""
    video_urls = set()
    
    def search_dict(d):
        """Recursively search through dictionary for video URLs"""
        nonlocal video_urls
        if not isinstance(d, dict):
            return
            
        for key, value in d.items():
            if isinstance(value, str) and any(x in value for x in ['.mp4', 'xhscdn.com/stream']):
                clean_url_value = clean_url(value)
                if clean_url_value.endswith('.mp4'):
                    video_urls.add(clean_url_value)
            
            elif key == 'masterUrl' or key == 'url' or key == 'originUrl':
                if isinstance(value, str):
                    clean_url_value = clean_url(value)
                    if clean_url_value.endswith('.mp4'):
                        video_urls.add(clean_url_value)
            
            elif key == 'backupUrls' and isinstance(value, list):
                for url in value:
                    if isinstance(url, str):
                        clean_url_value = clean_url(url)
                        if clean_url_value.endswith('.mp4'):
                            video_urls.add(clean_url_value)
            
            elif isinstance(value, dict):
                search_dict(value)
                
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        search_dict(item)
    
    try:
        search_dict(json_data)
        return list(video_urls)
    except Exception as e:
        logging.error(f"Error searching JSON: {e}")
        return []