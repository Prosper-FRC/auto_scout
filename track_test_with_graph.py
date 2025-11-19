from ultralytics import YOLO
import ffmpeg
import matplotlib.pyplot as plt
import numpy as np

input_file = 'test_traker.MOV'
output_file = 'test_lessfpstracker.mp4'
target_fps = 10

(
    ffmpeg
    .input(input_file)
    .filter('fps', fps=target_fps)
    .output(output_file)
    .run()
)

model = YOLO('yolo11n.pt')
results = model.track(source="test_lessfpstracker.mp4", show=True)

# Store coordinates for graphing
x_coords = []
y_coords = []
frame_numbers = []
tracked_labels = []  # Store labels for each frame

# Dictionary to map tracking IDs to custom labels (persists throughout video)
object_labels = {}  # {track_id: "custom_label"}
next_label_number = 1

# Each result has tracking IDs
frame_num = 0
for r in results:
    frame_num += 1
    
    if r.boxes.id is not None and len(r.boxes.id) > 0:
        # Get tracking IDs and center coordinates
        track_ids = r.boxes.id.cpu().numpy()
        centers = r.boxes.xywh.cpu().numpy()
        
        # Process each detected object in the frame
        for i, track_id in enumerate(track_ids):
            track_id_int = int(track_id)
            
            # Assign label on first appearance
            if track_id_int not in object_labels:
                object_labels[track_id_int] = f"Person_{next_label_number}"
                print(f"New object detected! Assigning label: {object_labels[track_id_int]} (Track ID: {track_id_int})")
                next_label_number += 1
            
            # Get the persistent label for this track ID
            label = object_labels[track_id_int]
            center_x, center_y = centers[i][0], centers[i][1]
            
            # Store coordinates (tracking all objects, or you can filter by label)
            x_coords.append(center_x)
            y_coords.append(center_y)
            frame_numbers.append(frame_num)
            tracked_labels.append(label)
            
            print(f"Frame {frame_num}: {label} (ID: {track_id_int}), Center: ({center_x:.1f}, {center_y:.1f})")

# Create graph after processing
if len(x_coords) > 0:
    plt.figure(figsize=(12, 8))
    
    # Plot 1: X position over time
    plt.subplot(2, 2, 1)
    plt.plot(frame_numbers, x_coords, 'b-', linewidth=2, marker='o', markersize=3)
    plt.xlabel('Frame Number')
    plt.ylabel('X Position (pixels)')
    plt.title('X Position Over Time')
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Y position over time
    plt.subplot(2, 2, 2)
    plt.plot(frame_numbers, y_coords, 'r-', linewidth=2, marker='o', markersize=3)
    plt.xlabel('Frame Number')
    plt.ylabel('Y Position (pixels)')
    plt.title('Y Position Over Time')
    plt.grid(True, alpha=0.3)
    
    # Plot 3: 2D path (X vs Y)
    plt.subplot(2, 2, 3)
    plt.plot(x_coords, y_coords, 'g-', linewidth=2, marker='o', markersize=4, alpha=0.7)
    plt.scatter(x_coords[0], y_coords[0], color='green', s=100, marker='s', label='Start', zorder=5)
    plt.scatter(x_coords[-1], y_coords[-1], color='red', s=100, marker='X', label='End', zorder=5)
    plt.xlabel('X Position (pixels)')
    plt.ylabel('Y Position (pixels)')
    plt.title('2D Path Trajectory')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.gca().invert_yaxis()  # Invert Y axis (since (0,0) is top-left in images)
    
    # Plot 4: Combined X and Y over time
    plt.subplot(2, 2, 4)
    plt.plot(frame_numbers, x_coords, 'b-', linewidth=2, label='X Position', marker='o', markersize=3)
    plt.plot(frame_numbers, y_coords, 'r-', linewidth=2, label='Y Position', marker='s', markersize=3)
    plt.xlabel('Frame Number')
    plt.ylabel('Position (pixels)')
    plt.title('X and Y Positions Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('tracking_path_graph.png', dpi=150, bbox_inches='tight')
    print(f"\nGraph saved as 'tracking_path_graph.png'")
    print(f"Total frames tracked: {len(x_coords)}")
    print(f"Path length: {len(x_coords)} points")
    print(f"\nObjects tracked: {list(object_labels.values())}")
    print(f"Label mapping: {object_labels}")
    
    plt.show()
else:
    print("No coordinates collected. Make sure objects were detected in the video.")
