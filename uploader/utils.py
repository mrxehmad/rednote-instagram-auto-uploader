#!/usr/bin/env python3
"""
Utility functions for the uploader module
"""
import os
import logging
import subprocess

def setup_logging(debug=False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def validate_video(video_path):
    """
    Validate that the video file exists and is a valid video
    
    Args:
        video_path (str): Path to the video file
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(video_path):
        logging.error(f"Video file not found: {video_path}")
        return False
        
    if not os.path.isfile(video_path):
        logging.error(f"Not a file: {video_path}")
        return False
        
    # Check if it's actually a video file using file extension
    _, ext = os.path.splitext(video_path)
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    
    if ext.lower() not in valid_extensions:
        logging.warning(f"File extension {ext} may not be a valid video format")
        
    # Try to get video metadata with ffprobe if available
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logging.warning("Failed to get video metadata, file might be corrupted")
            return False
            
        duration = float(result.stdout.strip())
        if duration < 0.1:
            logging.error("Video is too short (less than 0.1 seconds)")
            return False
            
        logging.debug(f"Video duration: {duration:.2f} seconds")
        
    except (subprocess.SubprocessError, FileNotFoundError):
        # ffprobe not available, skip this check
        logging.debug("ffprobe not available, skipping video validation")
        
    return True

def get_video_dimensions(video_path):
    """
    Get video dimensions using ffprobe
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        tuple: (width, height) or None if unable to get dimensions
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            video_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            dimensions = result.stdout.strip().split('x')
            width = int(dimensions[0])
            height = int(dimensions[1])
            return (width, height)
            
    except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError):
        pass
        
    return None