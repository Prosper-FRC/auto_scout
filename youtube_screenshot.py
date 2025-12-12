#!/usr/bin/env python3
"""
YouTube Video Screenshot Tool

Downloads a YouTube video and extracts a screenshot at a specified timestamp.
"""

import argparse
import os
import re
import sys

import ffmpeg
import yt_dlp

# ============================================================================
# CONFIGURATION - Set these variables to your preferences
# ============================================================================

# YouTube video URL
YOUTUBE_URL = "https://www.youtube.com/watch?v=ziu-iUGEPyg"  # Change this to your video URL

# Timestamp in timecode format: "HH:MM:SS", "MM:SS", or "SS" (seconds)
TIMESTAMP = "00:00:58"  # Change this to your desired timestamp

# Output directory for screenshots
OUTPUT_DIR = "singular-screenshot"  # Change this if you want a different output folder

# ============================================================================


def parse_timecode(timecode_string):
    """
    Parse timecode string to seconds.
    
    Supports formats:
    - "HH:MM:SS" (e.g., "00:01:30" = 90 seconds)
    - "MM:SS" (e.g., "1:30" = 90 seconds)
    - "SS" (e.g., "90" = 90 seconds)
    """
    timecode = timecode_string.strip()
    
    # Try to parse as seconds (just a number)
    try:
        return float(timecode)
    except ValueError:
        pass
    
    # Parse as timecode (HH:MM:SS or MM:SS)
    parts = timecode.split(':')
    
    if len(parts) == 3:
        # HH:MM:SS format
        hours, minutes, seconds = map(float, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        # MM:SS format
        minutes, seconds = map(float, parts)
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid timecode format: {timecode_string}. Use HH:MM:SS, MM:SS, or seconds")


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
        'restrictfilenames': False,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get title and duration
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            duration = info.get('duration', 0)
            
            # Download the video
            print(f"Downloading: {title}")
            ydl.download([url])
            
            # Find the downloaded file
            video_file = None
            for ext in ['mp4', 'mkv', 'webm', 'mov']:
                potential_file = os.path.join(output_dir, f"{title}.{ext}")
                if os.path.exists(potential_file):
                    video_file = potential_file
                    break
            
            if not video_file:
                # Try to find any recently downloaded file
                files = sorted([f for f in os.listdir(output_dir) 
                               if os.path.isfile(os.path.join(output_dir, f))],
                              key=lambda f: os.path.getmtime(os.path.join(output_dir, f)),
                              reverse=True)
                if files:
                    video_file = os.path.join(output_dir, files[0])
            
            if not video_file or not os.path.exists(video_file):
                print(f"Error: Could not locate downloaded video file")
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
        duration = float(probe['format']['duration'])
        return duration
    except:
        try:
            # Alternative method using subprocess
            import subprocess
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


def extract_screenshot(video_file, timestamp_seconds, output_path):
    """
    Extract a screenshot from video at specified timestamp.
    
    Args:
        video_file: Path to video file
        timestamp_seconds: Timestamp in seconds
        output_path: Path to save screenshot
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Extract frame using ffmpeg
        (
            ffmpeg
            .input(video_file, ss=timestamp_seconds)
            .output(output_path, vframes=1, **{'q:v': 2})  # High quality JPG
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
        return True
    except Exception as e:
        print(f"Error extracting screenshot: {e}")
        return False


def format_timestamp(seconds):
    """Format seconds as HH:MM:SS timecode."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main():
    parser = argparse.ArgumentParser(
        description='Extract screenshot from YouTube video at specified timestamp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use variables defined at top of script:
  python youtube_screenshot.py
  
  # Or override with command-line arguments:
  python youtube_screenshot.py --url "https://youtube.com/watch?v=VIDEO" --time "00:01:30"
  python youtube_screenshot.py --url URL --time "1:30" --output my_screenshots
        """
    )
    
    parser.add_argument('--url', default=YOUTUBE_URL,
                       help=f'YouTube video URL (default: from YOUTUBE_URL variable)')
    parser.add_argument('--time', '--timestamp', dest='timestamp', default=TIMESTAMP,
                       help=f'Timestamp in timecode format: "HH:MM:SS", "MM:SS", or seconds (default: {TIMESTAMP})')
    parser.add_argument('--output', '-o', default=OUTPUT_DIR,
                       help=f'Output directory for screenshot (default: {OUTPUT_DIR})')
    parser.add_argument('--keep-video', action='store_true',
                       help='Keep downloaded video after extracting screenshot (default: delete)')
    
    args = parser.parse_args()
    
    # Parse timestamp
    try:
        timestamp_seconds = parse_timecode(args.timestamp)
        print(f"Timestamp: {args.timestamp} = {timestamp_seconds:.2f} seconds ({format_timestamp(timestamp_seconds)})")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Download video
    print(f"\nProcessing: {args.url}")
    video_info = download_video(args.url)
    
    if not video_info or not video_info['file']:
        print("Failed to download video")
        sys.exit(1)
    
    video_file = video_info['file']
    video_title = video_info['title']
    video_duration = video_info.get('duration', 0)
    
    # Validate timestamp is within video duration
    if video_duration > 0 and timestamp_seconds > video_duration:
        print(f"Warning: Timestamp {timestamp_seconds:.2f}s exceeds video duration {video_duration:.2f}s")
        print("Screenshot will be taken at the end of the video")
        timestamp_seconds = max(0, video_duration - 0.1)
    
    # Get actual duration if not available from yt-dlp
    if video_duration == 0:
        video_duration = get_video_duration(video_file)
        if video_duration and timestamp_seconds > video_duration:
            print(f"Warning: Timestamp exceeds video duration {video_duration:.2f}s")
            timestamp_seconds = max(0, video_duration - 0.1)
    
    print(f"Video: {video_title}")
    print(f"Duration: {video_duration:.2f} seconds" if video_duration > 0 else "Duration: unknown")
    
    # Create output filename
    sanitized_title = sanitize_filename(video_title)
    timestamp_str = format_timestamp(timestamp_seconds).replace(':', '-')
    output_filename = f"{sanitized_title}_{timestamp_str}.jpg"
    output_path = os.path.join(args.output, output_filename)
    
    # Extract screenshot
    print(f"\nExtracting screenshot at {format_timestamp(timestamp_seconds)}...")
    success = extract_screenshot(video_file, timestamp_seconds, output_path)
    
    if success:
        print(f"✓ Screenshot saved to: {output_path}")
        
        # Clean up downloaded video if not keeping
        if not args.keep_video:
            try:
                os.remove(video_file)
                print("Cleaned up downloaded video")
            except:
                pass
    else:
        print("Failed to extract screenshot")
        sys.exit(1)


if __name__ == '__main__':
    main()

