# RedNote to Instagram Uploader

A Python tool that automatically downloads videos from RedNote (Xiaohongshu) and uploads them to Instagram as reels.

## Features

- Downloads videos from RedNote links
- Preserves original captions and hashtags
- Automatically uploads to Instagram as reels
- Supports continuous mode for automatic processing
- Handles Chinese characters and emojis properly
- Smart caption handling with fallback to random hashtags
- Automatic video format conversion for Instagram compatibility

> [!NOTE]  
>Currently, the tool may not work reliably due to two primary issues:
>
>1. **Old or expired RedNote links** – Some URLs may no longer be valid or accessible.
>2. **IP detection issues** – RedNote might be detecting and blocking certain IP ranges, including >residential IPs. Access may succeed occasionally, but is inconsistent.
>
>We're actively investigating possible workarounds. If you have experience with bypassing such >restrictions or would like to contribute solutions, **help is welcome!**

---

## Requirements

- Python 3.8 or higher
- Instagram account credentials
- Required Python packages (install using `pip install -r requirements.txt`):
  - instagrapi>=1.17.0
  - requests>=2.31.0
  - moviepy==1.0.3 (specific version required for instagrapi compatibility)
  - imageio-ffmpeg>=0.4.9
  - python-dotenv>=1.0.0
  - ffmpeg (system dependency)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mrxehmad/rednote-instagram-auto-uploader
cd rednote-instagram-auto-uploader
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

4. Set up your environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your credentials and settings:
     ```
     # Instagram credentials
     INSTAGRAM_USERNAME=your_username
     INSTAGRAM_PASSWORD=your_password

     # Optional settings
     DEBUG=false
     CONTINUOUS_MODE=false
     CHECK_INTERVAL=3600
     DOWNLOADS_DIR=downloads
     URL_FILE=urls.txt
     ```

## Usage

1. Create a `urls.txt` file with RedNote video URLs (one per line)

2. Run the script:
```bash
# Process URLs once
python main.py

# Run in continuous mode (checks for new URLs every hour)
python main.py --continuous

# Specify custom URL file and download directory
python main.py --url-file my_urls.txt --downloads-dir my_downloads
```

### Command Line Arguments

- `-u, --url-file`: File containing URLs to process (default: urls.txt)
- `-d, --downloads-dir`: Directory for downloaded videos (default: downloads)
- `-c, --continuous`: Run continuously, checking for new URLs
- `-i, --interval`: Interval in seconds between checks in continuous mode (default: 3600)
- `--debug`: Enable debug mode for detailed logging

Note: Command line arguments override settings in `.env` file.


## Security Notes

- Never commit your `.env` file or `session.pkl`
- Keep your Instagram credentials secure
- The script uses secure authentication methods
- All sensitive data is stored locally only
- Use environment variables for sensitive configuration

## Logging

The script generates two log files:
- `video_processor.log`: Main process logs
- `uploads.log`: Successful upload records

These files contain sensitive information and are automatically ignored by git.

## Notes

- The script preserves original captions and hashtags from RedNote
- Videos are automatically deleted after successful upload
- Instagram authentication is handled securely
- Supports both short and full RedNote URLs
- Smart caption handling with fallback to random hashtags
- Automatic video format conversion for Instagram compatibility
- Uses specific moviepy version (1.0.3) for compatibility with instagrapi

## Credits

- Built with [instagrapi](https://github.com/adw0rd/instagrapi) for Instagram API
- Uses [ffmpeg](https://ffmpeg.org/) for video processing
- Inspired by various RedNote downloader projects

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for educational purposes only. Please respect Instagram's terms of service and RedNote's content policies when using this tool.