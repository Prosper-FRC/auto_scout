from ultralytics import YOLO

import ffmpeg

input_file = "inputs/IMG_3089.MOV"
output_file = "inputs/test.mp4"
target_fps = 10

(
    ffmpeg
    .input(input_file)
    .filter('fps', fps=target_fps)
    .output(output_file)
    .run()
)

model = YOLO('models/yolo11n.pt')
results = model.track(source="inputs/test.mp4", show=True)

# Each result has tracking IDs
for r in results:
    # print(r.boxes.id)  # tracking IDs
    # print(r.boxes.xyxy)  # bounding boxes
    str1 = (str(r.boxes.xyxy))[9:len(str(r.boxes.xyxy)) - 3]
    points = str1.split(",")
    # for i in range(len(points)): points[i] = float(points[i])

    #if r.boxes.id == "tensor([12.])":
    print(r.boxes.id) 
    print(points)
    # print()
    # print()

    
