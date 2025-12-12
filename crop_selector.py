#!/usr/bin/env python3
"""
Crop Selection Tool

Interactive tool to select a crop region from an image by dragging a box.
Outputs crop parameters in "x:y:width:height" format for use in video_screenshot_extractor.py
"""

import argparse
import cv2
import os
import sys

# ============================================================================
# CONFIGURATION - Set this variable to your image path
# ============================================================================

IMAGE_PATH = 'test_crop.jpg'  # Change this to your image path

# ============================================================================

# Global variables for mouse callback
drawing = False
start_point = None
end_point = None
image = None
display_image = None


def mouse_callback(event, x, y, flags, param):
    """Handle mouse events for drawing selection rectangle."""
    global drawing, start_point, end_point, display_image, image
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_point = (x, y)
        end_point = (x, y)
        print(f"Selection started at ({x}, {y})")
    
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            end_point = (x, y)
            # Redraw image with current selection
            display_image = image.copy()
            if start_point and end_point:
                cv2.rectangle(display_image, start_point, end_point, (0, 255, 0), 2)
                # Show coordinates
                cv2.putText(display_image, f"({x}, {y})", (x + 5, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                # Show selection info
                x1, y1 = start_point
                x2, y2 = end_point
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                info_text = f"Selection: {w}x{h} - Press 'c' to confirm"
                cv2.putText(display_image, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow('Crop Selector - Click and drag to select region', display_image)
    
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_point = (x, y)
        print(f"Selection ended at ({x}, {y})")
        # Final rectangle
        display_image = image.copy()
        if start_point and end_point:
            cv2.rectangle(display_image, start_point, end_point, (0, 255, 0), 2)
            # Show selection info
            x1, y1 = start_point
            x2, y2 = end_point
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            if w > 0 and h > 0:
                info_text = f"Selection: {w}x{h} at ({min(x1,x2)}, {min(y1,y2)}) - Press 'c' to confirm"
                cv2.putText(display_image, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow('Crop Selector - Click and drag to select region', display_image)


def calculate_crop_params(start_point, end_point):
    """Calculate crop parameters from start and end points."""
    if not start_point or not end_point:
        return None
    
    x1, y1 = start_point
    x2, y2 = end_point
    
    # Ensure x1 < x2 and y1 < y2
    x = min(x1, x2)
    y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    return (x, y, width, height)


def format_crop_string(crop_params):
    """Format crop parameters as "x:y:width:height" string."""
    if not crop_params:
        return None
    x, y, width, height = crop_params
    return f"{x}:{y}:{width}:{height}"


def main():
    global image, display_image, start_point, end_point
    
    parser = argparse.ArgumentParser(
        description='Interactive tool to select crop region from an image',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use variable defined at top of script:
  python crop_selector.py
  
  # Or specify image path:
  python crop_selector.py image.jpg
  python crop_selector.py /path/to/image.png
        """
    )
    
    parser.add_argument('image_path', nargs='?', default=IMAGE_PATH,
                       help=f'Path to image file (default: {IMAGE_PATH})')
    
    args = parser.parse_args()
    
    # Load image
    image_path = args.image_path
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        print(f"Please set IMAGE_PATH variable at the top of the script or provide a file path")
        sys.exit(1)
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from '{image_path}'")
        print("Make sure the file is a valid image (JPG, PNG, etc.)")
        sys.exit(1)
    
    display_image = image.copy()
    
    # Get image dimensions
    height, width = image.shape[:2]
    print(f"Image loaded: {width}x{height} pixels")
    print("\nInstructions:")
    print("1. Click and drag to draw a selection rectangle")
    print("2. Press 'c' to confirm selection and get crop parameters")
    print("3. Press 'r' to reset selection")
    print("4. Press 'q' or ESC to quit")
    print()
    
    # Create window and set mouse callback
    window_name = 'Crop Selector - Click and drag to select region'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    # Display instructions on image
    instructions = [
        "Click and drag to select crop region",
        "Press 'c' to confirm, 'r' to reset, 'q' to quit"
    ]
    y_offset = 30
    for i, text in enumerate(instructions):
        cv2.putText(display_image, text, (10, y_offset + i * 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display_image, text, (10, y_offset + i * 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    cv2.imshow(window_name, display_image)
    
    # Main loop
    while True:
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == 27:  # 'q' or ESC
            print("Exiting...")
            break
        
        elif key == ord('c'):  # Confirm selection
            # Check if we have a valid selection (both points set and different)
            if start_point and end_point and start_point != end_point:
                crop_params = calculate_crop_params(start_point, end_point)
                crop_string = format_crop_string(crop_params)
                
                # Validate that we have a meaningful selection (width and height > 0)
                if crop_string and crop_params[2] > 0 and crop_params[3] > 0:
                    print("\n" + "="*50)
                    print("CROP PARAMETERS:")
                    print("="*50)
                    print(f"Format: x:y:width:height")
                    print(f"Output: {crop_string}")
                    print("="*50)
                    print("\nCopy this string to CROP_PARAMS in video_screenshot_extractor.py:")
                    print(f"CROP_PARAMS = \"{crop_string}\"")
                    print("="*50 + "\n")
                    
                    # Display on image
                    display_image = image.copy()
                    cv2.rectangle(display_image, start_point, end_point, (0, 255, 0), 3)
                    x, y, w, h = crop_params
                    info_text = f"Crop: {crop_string}"
                    cv2.putText(display_image, info_text, (10, height - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_image, "Press 'r' to reset, 'q' to quit", (10, height - 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.imshow(window_name, display_image)
                else:
                    print("Error: Invalid selection (width or height is 0). Please drag to create a selection box.")
            else:
                if not start_point or not end_point:
                    print("No selection made. Click and drag to select a region first.")
                elif start_point == end_point:
                    print("Selection is too small. Please click and drag to create a selection box.")
                else:
                    print("No valid selection. Please click and drag to select a region first.")
        
        elif key == ord('r'):  # Reset selection
            start_point = None
            end_point = None
            display_image = image.copy()
            # Redraw instructions
            for i, text in enumerate(instructions):
                cv2.putText(display_image, text, (10, y_offset + i * 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(display_image, text, (10, y_offset + i * 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            cv2.imshow(window_name, display_image)
            print("Selection reset. Click and drag to select a new region.")
    
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()

