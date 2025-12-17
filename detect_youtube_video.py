#!/usr/bin/env python3
"""
YOLO YouTube Video Detection Script

Downloads a YouTube video, crops it, and runs custom YOLO model detection on it.
"""

import os
import sys
import json
import cv2

import ffmpeg
import yt_dlp
from ultralytics import YOLO

# ============================================================================
# CONFIGURATION - Set these variables to your preferences
# ============================================================================

# YouTube video URL
YOUTUBE_URL = "https://www.youtube.com/watch?v=ziu-iUGEPyg"  # Change this to your video URL

# Crop parameters in format "x:y:width:height" (e.g., "66:219:1774:385")
CROP_PARAMS = "66:219:1774:385"  # Change this to your crop settings

# Output directory for detection results
OUTPUT_DIR = "outputs"  # Change this if you want a different output folder

# Temporary directory for downloaded and cropped videos
TEMP_DIR = "data/samples"  # Change this if you want a different temp folder

# Clean up temporary files after processing
CLEANUP_TEMP_FILES = True  # Set to False to keep downloaded and cropped videos

# ============================================================================


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


def crop_video(input_file, output_file, crop_params):
    """
    Crop video using ffmpeg.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output cropped video file
        crop_params: Tuple of (x, y, width, height) for cropping
    """
    x, y, width, height = crop_params
    
    try:
        print(f"Cropping video: x={x}, y={y}, width={width}, height={height}")
        (
            ffmpeg
            .input(input_file)
            .filter('crop', width, height, x, y)
            .output(output_file)
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
        print(f"Cropped video saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error cropping video: {e}")
        return False


def main():
    # Parse crop parameters
    crop_params = parse_crop(CROP_PARAMS)
    print(f"Crop parameters: x={crop_params[0]}, y={crop_params[1]}, "
          f"width={crop_params[2]}, height={crop_params[3]}")
    
    # Download video
    print(f"\nProcessing: {YOUTUBE_URL}")
    video_info = download_video(YOUTUBE_URL, TEMP_DIR)
    
    if not video_info or not video_info['file']:
        print("Failed to download video")
        sys.exit(1)
    
    downloaded_file = video_info['file']
    video_title = video_info['title']
    
    print(f"Video downloaded: {video_title}")
    print(f"File: {downloaded_file}")
    
    # Create cropped video filename
    base_name = os.path.splitext(os.path.basename(downloaded_file))[0]
    cropped_file = os.path.join(TEMP_DIR, f"{base_name}_cropped.mp4")
    
    # Crop video
    print(f"\nCropping video...")
    if not crop_video(downloaded_file, cropped_file, crop_params):
        print("Failed to crop video")
        sys.exit(1)
    
    # Load YOLO model
    print(f"\nLoading custom model...")
    model = YOLO('models/new_model/my_model.pt')
    
    # Run detection
    print(f"\nRunning detection on cropped video...")
    print(f"Results will be displayed and saved to: {OUTPUT_DIR}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get video FPS for timestamp calculation
    cap = cv2.VideoCapture(cropped_file)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30  # Default to 30 if FPS not available
    cap.release()
    print(f"Video FPS: {fps}")
    
    results = model.predict(
        source=cropped_file,
        show=True,
        save=True,
        project=OUTPUT_DIR
    )

    # Collect bounding boxes with timestamps
    detection_data = {}
    frame_number = 0
    
    for result in results:
        # Calculate timestamp based on frame number and FPS
        timestamp_seconds = frame_number / fps
        
        # Get bounding boxes
        boxes = result.boxes.xyxy.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int) if result.boxes.cls is not None else []
        
        # Store bounding boxes for this timestamp
        if len(boxes) > 0:
            detection_data[timestamp_seconds] = []
            for box, cid in zip(boxes, class_ids):
                x1, y1, x2, y2 = map(int, box)
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                width = x2 - x1
                height = y2 - y1
                class_name = result.names[cid] if hasattr(result, "names") and cid in result.names else str(cid)
                detection_data[timestamp_seconds].append({
                    "x,y": [center_x, center_y],
                    "width": width,
                    "height": height,
                    "bumper": class_name #blue-bumper red-bumper
                })
                print(f"Frame {frame_number} ({timestamp_seconds:.2f}s): ({x1}, {y1}) to ({x2}, {y2}) class={class_name}")
        
        frame_number += 1
    
    # Save to JSON file
    json_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(os.path.basename(cropped_file))[0]}_detections.json")
    with open(json_filename, 'w') as f:
        json.dump(detection_data, f, indent=2)
    
    print(f"\nDetection data saved to: {json_filename}")
    print(f"Total frames processed: {frame_number}")
    print(f"Frames with detections: {len(detection_data)}")
    print(f"\nDetection complete! Results saved to: {OUTPUT_DIR}")
    
    # Clean up temporary files if requested
    if CLEANUP_TEMP_FILES:
        print(f"\nCleaning up temporary files...")
        try:
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                print(f"Removed: {downloaded_file}")
            if os.path.exists(cropped_file):
                os.remove(cropped_file)
                print(f"Removed: {cropped_file}")
        except Exception as e:
            print(f"Warning: Could not remove some temporary files: {e}")
    else:
        print(f"\nTemporary files kept:")
        print(f"  Downloaded: {downloaded_file}")
        print(f"  Cropped: {cropped_file}")


if __name__ == '__main__':
    main()

