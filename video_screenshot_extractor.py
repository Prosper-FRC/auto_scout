#!/usr/bin/env python3
"""
YouTube Video Screenshot Extractor

Downloads YouTube videos, crops them, and extracts 10 evenly-spaced screenshots.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import ffmpeg
import yt_dlp

# ============================================================================
# CONFIGURATION - Set these variables to your preferences
# ============================================================================

# Path to the text file containing YouTube URLs (one per line)
URL_FILE = 'youtubelinks.txt'  # Change this to your file path

# Crop parameters in format "x:y:width:height" (e.g., "100:50:800:600")
CROP_PARAMS = "66:219:1774:385"  # Change this to your crop settings

# Output directory for screenshots
OUTPUT_DIR = 'video_screenshots'  # Change this if you want a different output folder

# Number of screenshots to extract
NUM_SCREENSHOTS = 10  # Change this if you want more/fewer screenshots

# Keep downloaded videos after processing? (True = keep, False = delete)
KEEP_VIDEOS = False  # Set to True if you want to keep the downloaded videos

# ============================================================================


def sanitize_filename(filename):
    """Remove or replace characters that are invalid in filenames."""
    # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def download_video(url, output_dir='data/samples'):
    """Download YouTube video and return video info."""
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'restrictfilenames': False,  # We'll sanitize manually
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get title
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            duration = info.get('duration', 0)
            
            # Download the video
            print(f"Downloading: {title}")
            ydl.download([url])
            
            # Find the downloaded file
            sanitized_title = sanitize_filename(title)
            video_file = None
            for ext in ['mp4', 'mkv', 'webm', 'mov']:
                potential_file = os.path.join(output_dir, f"{title}.{ext}")
                if os.path.exists(potential_file):
                    video_file = potential_file
                    break
            
            if not video_file:
                # Try to find any recently downloaded file
                files = sorted(Path(output_dir).glob('*'), key=os.path.getmtime, reverse=True)
                if files:
                    video_file = str(files[0])
            
            if not video_file or not os.path.exists(video_file):
                print(f"  Error: Could not locate downloaded video file")
                return None
            
            return {
                'file': video_file,
                'title': title,
                'duration': duration
            }
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


def get_video_duration(video_file):
    """Get video duration in seconds using ffprobe."""
    try:
        probe = ffmpeg.probe(video_file)
        # Get duration from format section
        duration = float(probe['format']['duration'])
        return duration
    except:
        try:
            # Alternative method using subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', video_file],
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except:
            return None


def extract_screenshots(video_file, output_dir, crop_params, num_screenshots=10):
    """
    Extract screenshots from video at evenly spaced intervals.
    
    Args:
        video_file: Path to video file
        output_dir: Directory to save screenshots
        crop_params: Tuple of (x, y, width, height) for cropping
        num_screenshots: Number of screenshots to extract
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Validate video file exists
    if not os.path.exists(video_file):
        print(f"  Error: Video file not found: {video_file}")
        return
    
    # Get video duration
    duration = get_video_duration(video_file)
    if duration is None or duration <= 0:
        print(f"  Warning: Could not get duration for {video_file}, using default 60s")
        duration = 60  # Default to 60 seconds
    else:
        print(f"  Video duration: {duration:.2f} seconds")
    
    # Calculate timestamps (evenly spaced from start to end)
    # Distribute evenly: at 0%, 11.11%, 22.22%... 100% for 10 screenshots
    # Or more precisely: (i-1) / (n-1) for i from 1 to n
    timestamps = []
    if num_screenshots == 1:
        timestamps = [duration / 2]  # Middle of video
    else:
        for i in range(1, num_screenshots + 1):
            # Calculate position: 0% to 100% evenly spaced
            position = (i - 1) / (num_screenshots - 1) if num_screenshots > 1 else 0
            timestamp = duration * position
            # Ensure we don't go beyond video length
            timestamp = min(timestamp, duration - 0.1)
            timestamps.append(timestamp)
    
    x, y, width, height = crop_params
    
    # Extract screenshots
    for idx, timestamp in enumerate(timestamps, 1):
        screenshot_path = os.path.join(output_dir, f'screenshot_{idx:02d}.jpg')
        
        try:
            # Use ffmpeg to extract frame with crop
            (
                ffmpeg
                .input(video_file, ss=timestamp)
                .filter('crop', width, height, x, y)
                .output(screenshot_path, vframes=1, **{'q:v': 2})  # High quality JPG
                .overwrite_output()
                .run(quiet=True, capture_stderr=True)
            )
            print(f"  Extracted screenshot {idx}/{num_screenshots} at {timestamp:.2f}s ({timestamp/duration*100:.1f}%)")
        except Exception as e:
            print(f"  Error extracting screenshot {idx}: {e}")
            # Continue with next screenshot


def parse_crop(crop_string):
    """Parse crop string in format 'x:y:width:height'."""
    try:
        parts = crop_string.split(':')
        if len(parts) != 4:
            raise ValueError("Crop must be in format 'x:y:width:height'")
        return tuple(int(p) for p in parts)
    except Exception as e:
        print(f"Error parsing crop: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube videos and extract cropped screenshots',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use variables defined at top of script (just run it):
  python video_screenshot_extractor.py
  
  # Or override with command-line arguments:
  python video_screenshot_extractor.py urls.txt --crop "100:50:800:600"
  python video_screenshot_extractor.py urls.txt --crop "0:0:1920:1080" --output video_screenshots
        """
    )
    
    parser.add_argument('url_file', nargs='?', default=URL_FILE,
                       help=f'Text file containing YouTube URLs (default: {URL_FILE})')
    parser.add_argument('--crop', default=CROP_PARAMS,
                       help=f'Crop parameters in format "x:y:width:height" (default: {CROP_PARAMS})')
    parser.add_argument('--output', '-o', default=OUTPUT_DIR,
                       help=f'Output directory for screenshots (default: {OUTPUT_DIR})')
    parser.add_argument('--screenshots', '-n', type=int, default=NUM_SCREENSHOTS,
                       help=f'Number of screenshots to extract (default: {NUM_SCREENSHOTS})')
    parser.add_argument('--keep-videos', action='store_true',
                       help='Keep downloaded videos after processing (default: delete)')
    
    args = parser.parse_args()
    
    # Use default keep_videos setting if not specified via command line
    keep_videos = args.keep_videos if args.keep_videos else KEEP_VIDEOS
    
    # Parse crop parameters
    crop_params = parse_crop(args.crop)
    print(f"Crop parameters: x={crop_params[0]}, y={crop_params[1]}, "
          f"width={crop_params[2]}, height={crop_params[3]}")
    
    # Read URLs from file
    if not os.path.exists(args.url_file):
        print(f"Error: File '{args.url_file}' not found")
        print(f"Please set URL_FILE variable at the top of the script or provide a file path")
        sys.exit(1)
    
    with open(args.url_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print("No URLs found in file")
        sys.exit(1)
    
    print(f"Found {len(urls)} video(s) to process\n")
    
    # Process each video
    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] Processing: {url}")
        
        # Download video
        video_info = download_video(url)
        if not video_info or not video_info['file']:
            print(f"  Failed to download video, skipping...")
            continue
        
        video_file = video_info['file']
        video_title = video_info['title']
        sanitized_title = sanitize_filename(video_title)
        
        # Create output directory for this video
        video_output_dir = os.path.join(args.output, sanitized_title)
        
        # Extract screenshots
        print(f"  Extracting {args.screenshots} screenshots...")
        extract_screenshots(video_file, video_output_dir, crop_params, args.screenshots)
        
        # Clean up downloaded video if not keeping
        if not keep_videos:
            try:
                os.remove(video_file)
                print(f"  Cleaned up downloaded video")
            except:
                pass
        
        print(f"  ✓ Completed: {video_title}")
        print(f"  Screenshots saved to: {video_output_dir}")
    
    print(f"\n✓ All videos processed! Screenshots saved to: {args.output}")


if __name__ == '__main__':
    main()

