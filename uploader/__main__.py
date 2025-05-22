#!/usr/bin/env python3
"""
Main module for uploader package, providing command-line interface
"""
import sys
import argparse
from .upload import upload_reel

def main():
    """
    Command-line entry point for the uploader
    """
    parser = argparse.ArgumentParser(description='Instagram Reels Uploader')
    parser.add_argument('-v', '--video', required=True, help='Path to video file to upload')
    parser.add_argument('-c', '--caption', default='#reels', help='Caption for the video')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Upload the video
    upload_result = upload_reel(args.video, args.caption, debug=args.debug)
    
    if upload_result:
        print(f"Upload successful! Media ID: {upload_result}")
    else:
        print("Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()