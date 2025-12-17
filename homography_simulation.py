import cv2
import numpy as np
import json
import ast

# === SETTINGS ===
JSON_FILE = 'data.json'          # Your YOLO output file
SOURCE_IMG = 'camera_view.jpg'   # A screenshot from your video
MAP_IMG = 'top_down.png'        # A top-down image of the FRC field
OUTPUT_VIDEO = 'scouting_output.mp4'

def get_points(image, title):
    """Helper to let user click 4 points on an image."""
    points = []
    
    def click_event(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow(title, image)
            points.append([x, y])

    print(f"Click 4 corners on the {title} window...")
    cv2.imshow(title, image)
    cv2.setMouseCallback(title, click_event)
    
    # Wait until 4 points are clicked
    while len(points) < 4:
        cv2.waitKey(1)
    
    cv2.destroyAllWindows()
    return np.float32(points)

def main():
    # 1. Load Images
    src_img = cv2.imread(SOURCE_IMG)
    dst_img = cv2.imread(MAP_IMG)
    height, width, _ = dst_img.shape

    # 2. Calibration (User clicks 4 points on each image)
    # Hint: Click field corners in the SAME ORDER for both (e.g., TL, TR, BR, BL)
    print("Step 1: Calibration")
    src_pts = get_points(src_img.copy(), "Source (Camera View)")
    dst_pts = get_points(dst_img.copy(), "Destination (Top-Down Map)")

    # Calculate Homography Matrix
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    print("Homography calculated!")

    # 3. Load Data
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)

    # Sort timestamps to ensure video flows correctly
    timestamps = sorted(data.keys(), key=lambda x: float(x))

    # 4. Setup Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, 30.0, (width, height))

    print(f"Processing {len(timestamps)} frames...")

    for ts in timestamps:
        # Create a fresh frame from the map image
        frame = dst_img.copy()
        
        boxes = data[ts]
        
        points_to_transform = []
        
        # Extract "footprint" points from boxes
        # We use the bottom-center of the box (x_mid, y2) as the robot's location
        for box in boxes:
            x_center = (box['x1'] + box['x2']) / 2
            y_bottom = box['y2']
            points_to_transform.append([x_center, y_bottom])

        if points_to_transform:
            # Convert to numpy array and reshape to (N, 1, 2) format required by perspectiveTransform
            points_np = np.array(points_to_transform, dtype=np.float32).reshape(-1, 1, 2)
            
            # === THE MAGIC: Apply Perspective Transform ===
            transformed_points = cv2.perspectiveTransform(points_np, matrix)

            # Draw on map
            for pt in transformed_points:
                x_map, y_map = int(pt[0][0]), int(pt[0][1])
                
                # Draw robot (Green Dot)
                cv2.circle(frame, (x_map, y_map), 10, (0, 255, 0), -1)
                # Draw ID or Box (optional)
                cv2.rectangle(frame, (x_map-10, y_map-10), (x_map+10, y_map+10), (0, 255, 0), 2)

        # Write text timestamp
        cv2.putText(frame, f"Time: {float(ts):.2f}s", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)

    out.release()
    print(f"Done! Video saved as {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()