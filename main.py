#!/usr/bin/env python3
import os
import sys
import time
import logging
import argparse
from datetime import datetime
import re
import subprocess
import random

# Add the project directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from downloader.download import download_video_from_url
from uploader.upload import upload_reel

# Set up logging with proper encoding
LOG_FILE = "video_processor.log"
# Configure console handler with UTF-8 encoding
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Configure file handler with UTF-8 encoding
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

def sanitize_filename(filename):
    """
    Sanitize filename by removing special characters and hashtags
    """
    # Remove file extension
    name, ext = os.path.splitext(filename)
    
    # Remove hashtags and any special characters that might cause issues
    # Keep only alphanumeric characters, spaces, and basic punctuation
    sanitized = re.sub(r'[#@]', '', name)  # Remove hashtags and @ symbols
    sanitized = re.sub(r'[^\w\s\-\.]', '', sanitized)  # Keep only alphanumeric, spaces, hyphens, and dots
    
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return f"{sanitized}{ext}"

def convert_video_format(input_path, output_path=None):
    """
    Convert video to Instagram-compatible format using ffmpeg
    """
    if output_path is None:
        output_path = input_path.replace('.mp4', '_converted.mp4')
    
    try:
        # FFmpeg command to convert video to Instagram-compatible format
        # -c:v libx264: Use H.264 codec
        # -preset medium: Balance between quality and encoding speed
        # -crf 23: Constant Rate Factor (18-28 is good, lower is better quality)
        # -c:a aac: Use AAC audio codec
        # -b:a 128k: Audio bitrate
        # -movflags +faststart: Enable fast start for web playback
        # -vf scale=1080:1920:force_original_aspect_ratio=decrease: Add padding to maintain aspect ratio
        # -pix_fmt yuv420p: Ensure pixel format compatibility
        # -r 30: Set frame rate to 30fps
        # -b:v 2M: Set video bitrate to 2Mbps
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            '-b:v', '2M',
            output_path
        ]
        
        logging.info(f"Converting video format: {input_path} -> {output_path}")
        
        # Use subprocess.Popen to handle Unicode output properly
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg conversion failed: {stderr}")
            return None
        
        logging.info("Video conversion successful")
        return output_path
        
    except Exception as e:
        logging.error(f"Error converting video: {e}")
        return None

def get_random_hashtags(num_tags=2):
    """
    Get random hashtags from tags.txt
    """
    try:
        with open('tags.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            hashtags = content.split()
            if len(hashtags) >= num_tags:
                return ' '.join(random.sample(hashtags, num_tags))
            return ' '.join(hashtags)
    except Exception as e:
        logging.error(f"Error reading tags.txt: {e}")
        return "#reels #trending"

def process_url_file(url_file="urls.txt", downloads_dir="downloads", debug=False):
    """
    Process URLs from the url file one by one, downloading and uploading each video
    """
    # Create downloads directory if it doesn't exist
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
    
    if not os.path.exists(url_file):
        logging.error(f"URL file not found: {url_file}")
        return False
    
    try:
        with open(url_file, "r", encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            logging.warning(f"No URLs found in {url_file}")
            return False
        
        logging.info(f"Found {len(urls)} URLs to process")
        
        # Process the first URL in the file
        url = urls[0]
        logging.info(f"Processing URL: {url}")
        
        # Download the video and get caption
        video_path = download_video_from_url(url, downloads_dir, debug=debug)
        
        if not video_path:
            logging.error("Failed to download video")
            return False
        
        # Get the caption from the video filename
        filename = os.path.basename(video_path)
        # Convert underscores back to spaces for the caption
        caption = os.path.splitext(filename)[0].replace('_', ' ')
        
        # Check if the caption is the default "hs_www.xiaohongshu.com"
        if caption == "hs_www.xiaohongshu.com":
            # Use random hashtags from tags.txt
            caption = get_random_hashtags()
        # If no hashtags are present, add random hashtags
        elif not any(tag in caption for tag in ['#', 'hashtag']):
            # If caption is empty or just whitespace, use only random hashtags
            if not caption.strip():
                caption = get_random_hashtags()
            else:
                caption = f"{caption} {get_random_hashtags()}"
        
        # Clean up the caption
        caption = caption.strip()
        # Remove any duplicate hashtags
        hashtags = set(re.findall(r'#\w+', caption))
        caption = re.sub(r'#\w+\s*', '', caption).strip()  # Remove all hashtags
        caption = f"{caption} {' '.join(sorted(hashtags))}".strip()  # Add back unique hashtags
        
        logging.info(f"Using caption: {caption}")
        
        # Sanitize the video filename before upload
        sanitized_path = os.path.join(os.path.dirname(video_path), sanitize_filename(os.path.basename(video_path)))
        if video_path != sanitized_path:
            os.rename(video_path, sanitized_path)
            video_path = sanitized_path
            logging.info(f"Renamed video file to: {video_path}")
        
        # Convert video to Instagram-compatible format
        converted_path = convert_video_format(video_path)
        if converted_path:
            # Delete original video
            os.remove(video_path)
            video_path = converted_path
            logging.info(f"Using converted video: {video_path}")
        
        # Upload the video
        upload_result = upload_reel(video_path, caption, debug=debug)
        
        if upload_result:
            # Log the successful upload
            log_upload(url, video_path, upload_result)
            
            # Remove the processed URL from the file
            remove_url_from_file(url_file, url)
            
            # Delete the downloaded video file
            os.remove(video_path)
            logging.info(f"Deleted downloaded video: {video_path}")
            
            return True
        else:
            logging.error("Upload failed")
            return False
            
    except Exception as e:
        logging.error(f"Error processing URL file: {e}")
        return False

def log_upload(url, video_path, upload_info):
    """
    Log the upload details to a separate log file
    """
    upload_log_file = "uploads.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = (
        f"TIME: {timestamp}\n"
        f"URL: {url}\n"
        f"VIDEO: {video_path}\n"
        f"UPLOAD_ID: {upload_info}\n"
        f"{'-' * 50}\n"
    )
    
    with open(upload_log_file, "a", encoding='utf-8') as f:
        f.write(log_entry)
    
    logging.info(f"Upload logged to {upload_log_file}")

def remove_url_from_file(url_file, processed_url):
    """
    Remove the processed URL from the url file
    """
    try:
        with open(url_file, "r", encoding='utf-8') as f:
            urls = [line.strip() for line in f]
        
        with open(url_file, "w", encoding='utf-8') as f:
            for url in urls:
                if url.strip() != processed_url:
                    f.write(f"{url}\n")
        
        logging.info(f"Removed processed URL from {url_file}")
    except Exception as e:
        logging.error(f"Error removing URL from file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Download and upload videos from URLs')
    parser.add_argument('-u', '--url-file', default='urls.txt', help='File containing URLs to process')
    parser.add_argument('-d', '--downloads-dir', default='downloads', help='Directory for downloaded videos')
    parser.add_argument('-c', '--continuous', action='store_true', help='Run continuously, checking for new URLs')
    parser.add_argument('-i', '--interval', type=int, default=3600, help='Interval in seconds between checks in continuous mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for detailed logging')
    
    args = parser.parse_args()
    
    if args.continuous:
        logging.info(f"Starting continuous mode, checking every {args.interval} seconds")
        
        while True:
            if os.path.exists(args.url_file) and os.path.getsize(args.url_file) > 0:
                process_url_file(args.url_file, args.downloads_dir, debug=args.debug)
            else:
                logging.info(f"No URLs to process. Waiting for next check.")
            
            logging.info(f"Sleeping for {args.interval} seconds")
            time.sleep(args.interval)
    else:
        # Run once
        process_url_file(args.url_file, args.downloads_dir, debug=args.debug)

if __name__ == "__main__":
    logging.info("Starting video processor")
    main()
    logging.info("Video processor finished")