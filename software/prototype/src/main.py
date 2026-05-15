import cv2
import pyzed.sl as sl
from pipeline import open_svo, grab_frame, load_model, detect

SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2"
OUTPUT_PATH = "/app/output_detections.mp4"

cam = open_svo(SVO_PATH)
print("Camera opened OK")

model = load_model("yolov8x.pt")
print("Model loaded OK")

writer = cv2.VideoWriter(OUTPUT_PATH, cv2.VideoWriter_fourcc(*"mp4v"), 30, (1920, 1080))

mat_rgb  = sl.Mat()
mat_xyz  = sl.Mat()
mat_conf = sl.Mat()

ball_id       = 0
frames_missing = 0
MAX_GAP       = 20

i = 0
while True:
    result = grab_frame(cam, mat_rgb, mat_xyz, mat_conf)
    if result is None:
        print("End of file")
        break

    left_rgb, xyz_map, conf_map = result
    detection = detect(model, left_rgb)
    i += 1

    frame_bgr = cv2.cvtColor(left_rgb, cv2.COLOR_RGB2BGR)

    if detection is None:
        frames_missing += 1
        print(f"Frame {i}: no ball detected (missing {frames_missing})")
    else:
        cx, cy = detection
        if frames_missing > MAX_GAP:
            ball_id += 1
        frames_missing = 0

        x, y, z, _ = xyz_map[cy, cx]
        label = f"ID:{ball_id}  x:{x:.2f}  y:{y:.2f}  z:{z:.2f}m"
        cv2.circle(frame_bgr, (cx, cy), 20, (255, 0, 0), 3)
        cv2.putText(frame_bgr, label, (cx + 25, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        print(f"Frame {i}: ID={ball_id}  ({cx},{cy})  x={x:.2f} y={y:.2f} z={z:.2f}m")

    writer.write(frame_bgr)

writer.release()
cam.close()
print(f"\nSaved to {OUTPUT_PATH}")