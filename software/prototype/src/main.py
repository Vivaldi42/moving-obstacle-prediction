import cv2
import pyzed.sl as sl
from pipeline import open_svo, grab_frame, load_model, detect

SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2"
OUTPUT_PATH = "/app/output_detections.mp4"

cam = open_svo(SVO_PATH)
print("Camera opened OK")

model = load_model("yolov8x.pt")
print("Model loaded OK")

writer = cv2.VideoWriter(OUTPUT_PATH, cv2.VideoWriter.fourcc(*"mp4v"), 30, (1920, 1080))
mat_rgb = sl.Mat()

prev_cx, prev_cy = None, None
cx, cy = None, None
missed = 0
MAX_EXTRAP = 5

i = 0
while True:
    left_rgb = grab_frame(cam, mat_rgb)
    if left_rgb is None:
        print("End of file")
        break

    i += 1
    frame_bgr = cv2.cvtColor(left_rgb, cv2.COLOR_RGB2BGR)

    detection = detect(model, left_rgb)

    if detection is not None:
        prev_cx, prev_cy = cx, cy
        cx, cy = detection
        missed = 0
        cv2.circle(frame_bgr, (cx, cy), 20, (0, 255, 0), 3)
        cv2.putText(frame_bgr, f"({cx}, {cy})", (cx + 25, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        print(f"Frame {i}: ({cx}, {cy})")
    elif cx is not None and cy is not None and prev_cx is not None and prev_cy is not None and missed < MAX_EXTRAP:
        vx = cx - prev_cx
        vy = cy - prev_cy
        prev_cx, prev_cy = cx, cy
        cx = cx + vx
        cy = cy + vy
        missed += 1
        cv2.circle(frame_bgr, (cx, cy), 20, (0, 165, 255), 3)
        cv2.putText(frame_bgr, f"({cx}, {cy}) [extrap]", (cx + 25, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        print(f"Frame {i}: ({cx}, {cy}) [extrapolated]")
    else:
        missed += 1
        print(f"Frame {i}: no ball")

    writer.write(frame_bgr)

writer.release()
cam.close()
print(f"\nSaved to {OUTPUT_PATH}")
