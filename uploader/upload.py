#!/usr/bin/env python3
"""
Upload module for uploading videos to Instagram
"""
import os
import logging
from .auth import create_client
from .utils import validate_video

def upload_reel(video_path, caption, debug=False):
    """
    Upload a video as a reel to Instagram
    
    Args:
        video_path (str): Path to the video file.
        caption (str): Caption for the reel.
        debug (bool): Enable debug mode
    
    Returns:
        str/None: Media ID if successful, None otherwise
    """
    # Validate that the video file exists and is valid
    if not validate_video(video_path):
        logging.error(f"Invalid video: {video_path}")
        return None
        
    # Get authenticated client
    client = create_client(debug)
    if not client:
        logging.error("Failed to create authenticated client")
        return None
        
    try:
        logging.info(f"Uploading reel: {video_path}")
        
        # Add some hashtags if not present
        if not any(tag in caption for tag in ['#', 'hashtag']):
            caption = f"{caption} #reels #trending"
            
        # Get video details for logging
        try:
            from moviepy.editor import VideoFileClip
            video = VideoFileClip(video_path)
            logging.info(f"Video details - Duration: {video.duration:.2f}s, Size: {video.size}, FPS: {video.fps}")
            video.close()
        except Exception as e:
            logging.warning(f"Could not get video details: {e}")
            
        # Upload as reel/clip
        try:
            media = client.clip_upload(video_path, caption)
            # Extract media ID
            media_id = media.id if hasattr(media, 'id') else str(media)
            logging.info(f"Reel uploaded successfully. Media ID: {media_id}")
            return media_id
        except Exception as upload_error:
            # Get detailed error information
            error_details = {
                'error_type': type(upload_error).__name__,
                'error_message': str(upload_error),
                'video_path': video_path,
                'video_size': os.path.getsize(video_path) / (1024 * 1024),  # Size in MB
                'caption_length': len(caption)
            }
            
            # Log detailed error information
            logging.error("Upload failed with details:")
            for key, value in error_details.items():
                logging.error(f"  {key}: {value}")
                
            # Check for specific error types
            if 'response' in str(upload_error):
                logging.error("Instagram API response error - This might be due to:")
                logging.error("1. Video format not supported")
                logging.error("2. Video duration too long/short")
                logging.error("3. Video size too large")
                logging.error("4. Rate limiting from Instagram")
            
            raise  # Re-raise the exception to be caught by outer try-except
        
    except Exception as e:
        logging.error(f"Failed to upload reel: {e}")
        if debug:
            import traceback
            logging.error("Full error traceback:")
            logging.error(traceback.format_exc())
        return None