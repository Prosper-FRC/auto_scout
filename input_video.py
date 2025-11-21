import yt_dlp as yt
import os
import argparse
import ffmpeg

def download_video(url, output_dir='inputs', output_format='mkv', quality='best', 
                  fps=None, restrict_filenames=True, custom_filename=None):
    """
    Download a YouTube video with customizable options.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the video
        output_format: Video format (mkv, mp4, webm, etc.)
        quality: Video quality ('best', 'worst', '720p', '1080p', etc. or format code)
        fps: Target frame rate (None = original, or specify like 10, 30, etc.)
        restrict_filenames: Remove special characters from filename
        custom_filename: Custom output filename (without extension)
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine output filename
    if custom_filename:
        output_file = f"{output_dir}/{custom_filename}.{output_format}"
    else:
        output_file = f"{output_dir}/%(title)s.%(ext)s"
    
    # Configure yt-dlp options
    opts = {
        'outtmpl': output_file,
        'restrictfilenames': restrict_filenames,
    }
    
    # Set quality/format selection
    if quality == 'best':
        opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif quality == 'worst':
        opts['format'] = 'worst'
    elif quality.isdigit():
        # Format code (e.g., '137' for 1080p video)
        opts['format'] = quality
    else:
        # Try to match quality string (e.g., '720p', '1080p')
        opts['format'] = f'bestvideo[height<={quality.replace("p", "")}]+bestaudio/best[height<={quality.replace("p", "")}]'
    
    print(f"Downloading video from: {url}")
    print(f"Output directory: {output_dir}")
    print(f"Format: {output_format}")
    print(f"Quality: {quality}")
    if fps:
        print(f"Target FPS: {fps}")
    print()
    
    # Download the video
    with yt.YoutubeDL(opts) as ydl:
        ydl.download([url])
    
    # If FPS is specified, process the video to change frame rate
    if fps:
        # Find the downloaded file
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'video')
        # Clean filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if restrict_filenames:
            safe_title = safe_title.replace(' ', '_')
        
        input_file = f"{output_dir}/{safe_title}.{output_format}"
        output_file_fps = f"{output_dir}/{safe_title}_{fps}fps.{output_format}"
        
        # Check if file exists (yt-dlp might have modified the name)
        if not os.path.exists(input_file):
            # Try to find the actual downloaded file
            files = [f for f in os.listdir(output_dir) if f.endswith(f'.{output_format}')]
            if files:
                input_file = f"{output_dir}/{files[-1]}"  # Use most recent
        
        if os.path.exists(input_file):
            print(f"\nConverting frame rate to {fps} fps...")
            (
                ffmpeg
                .input(input_file)
                .filter('fps', fps=fps)
                .output(output_file_fps)
                .overwrite_output()
                .run(quiet=True)
            )
            print(f"Saved as: {output_file_fps}")
        else:
            print(f"Warning: Could not find downloaded file to process FPS")

def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube videos with customizable quality and frame rate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download best quality, original FPS
  python input_video.py https://www.youtube.com/watch?v=VIDEO_ID
  
  # Download 720p at 10 fps
  python input_video.py https://www.youtube.com/watch?v=VIDEO_ID --quality 720p --fps 10
  
  # Download to custom location with custom name
  python input_video.py URL --output-dir data/samples --filename my_video --fps 30
        """
    )
    
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output-dir', '-o', default='inputs', 
                       help='Output directory (default: inputs)')
    parser.add_argument('--format', '-f', default='mkv', 
                       choices=['mkv', 'mp4', 'webm'],
                       help='Video format (default: mkv)')
    parser.add_argument('--quality', '-q', default='best',
                       help='Video quality: best, worst, 720p, 1080p, or format code (default: best)')
    parser.add_argument('--fps', type=int, default=None,
                       help='Target frame rate (e.g., 10, 30). If not specified, uses original FPS')
    parser.add_argument('--filename', '-n', default=None,
                       help='Custom output filename (without extension)')
    parser.add_argument('--no-restrict-filenames', action='store_true',
                       help='Allow special characters in filename')
    
    args = parser.parse_args()
    
    download_video(
        url=args.url,
        output_dir=args.output_dir,
        output_format=args.format,
        quality=args.quality,
        fps=args.fps,
        restrict_filenames=not args.no_restrict_filenames,
        custom_filename=args.filename
    )

if __name__ == '__main__':
    # Define constants for download_video function parameters
    DEFAULT_URL = 'https://www.youtube.com/watch?v=jMqu_nXhYQI'
    DEFAULT_OUTPUT_DIR = 'inputs'
    DEFAULT_OUTPUT_FORMAT = 'mkv'
    DEFAULT_QUALITY = 'best'
    DEFAULT_FPS = 10
    DEFAULT_RESTRICT_FILENAMES = True
    DEFAULT_CUSTOM_FILENAME = "video"
    download_video(
        url=DEFAULT_URL,
        output_dir=DEFAULT_OUTPUT_DIR,
        output_format=DEFAULT_OUTPUT_FORMAT,
        quality=DEFAULT_QUALITY,
        fps=DEFAULT_FPS,
        restrict_filenames=DEFAULT_RESTRICT_FILENAMES,
        custom_filename=DEFAULT_CUSTOM_FILENAME
    )
