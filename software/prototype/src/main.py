import cv2
import pyzed.sl as sl
from collections import deque
from pipeline import (
    open_svo,
    get_intrinsics,
    grab_frame,
    load_model,
    detect,
    resolve_xyz,
    project_to_pixel,
    BallKalmanFilter,
)


SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_one_ball_hit_window_21-35-59.svo2"

OUTPUT_PATH = "/app/output_detections.mp4"
PREDICTION_HORIZON = 0.2
MAX_MISS = 5

cam = open_svo(SVO_PATH)
print("Camera opened OK")

model = load_model("yolov8x.pt")
print("Model loaded OK")

fx, fy, cx_cam, cy_cam = get_intrinsics(cam)
kf = BallKalmanFilter(dt=1 / 30)
writer = cv2.VideoWriter(OUTPUT_PATH, cv2.VideoWriter.fourcc(*"mp4v"), 30, (1920, 1080))
mat_rgb = sl.Mat()
mat_xyz = sl.Mat()

missed = 0
history: deque[tuple[int, int]] = deque(maxlen=10)

i = 0
while True:
    result = grab_frame(cam, mat_rgb, mat_xyz)
    if result is None:
        print("End of file")
        break

    left_rgb, xyz_map = result
    i += 1
    frame_bgr = cv2.cvtColor(left_rgb, cv2.COLOR_RGB2BGR)

    pred_x, pred_y, pred_z = 0.0, 0.0, 0.0
    if kf.initialized:
        pred_x, pred_y, pred_z = kf.predict()

    detection = detect(model, left_rgb)

    if detection is not None:
        cx, cy = detection
        xyz = resolve_xyz(xyz_map, cx, cy)

        if xyz is not None:
            x, y, z = xyz
            if not kf.initialized:
                kf.init(x, y, z)
                pred_x, pred_y, pred_z = kf.predict()
            x, y, z = kf.correct(x, y, z)
            missed = 0
            history.append((cx, cy))
            label = f"x:{x:.2f} y:{y:.2f} z:{z:.2f}m"
            print(f"Frame {i}: ({cx}, {cy})  {label}")
            cv2.circle(frame_bgr, (cx, cy), 20, (0, 255, 0), 3)
            cv2.putText(frame_bgr, label, (cx + 25, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            missed = 0
            history.append((cx, cy))
            print(f"Frame {i}: ({cx}, {cy})  no depth")
            cv2.circle(frame_bgr, (cx, cy), 20, (0, 255, 0), 3)

    elif kf.initialized and missed < MAX_MISS:
        missed += 1
        pixel = project_to_pixel(pred_x, pred_y, pred_z, fx, fy, cx_cam, cy_cam)
        if pixel is not None:
            cx, cy = pixel
            history.append((cx, cy))
            label = f"x:{pred_x:.2f} y:{pred_y:.2f} z:{pred_z:.2f}m [kf]"
            print(f"Frame {i}: ({cx}, {cy})  {label}")
            cv2.circle(frame_bgr, (cx, cy), 20, (0, 165, 255), 3)
            cv2.putText(frame_bgr, label, (cx + 25, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        else:
            print(f"Frame {i}: no ball (kf out of frame)")

    else:
        missed += 1
        print(f"Frame {i}: no ball")

    for j in range(1, len(history)):
        cv2.line(frame_bgr, history[j - 1], history[j], (255, 0, 0), 5)

    if kf.initialized and len(history) > 0:
        fx_p, fy_p, fz_p = kf.predict_ahead(PREDICTION_HORIZON)
        pred_pixel = project_to_pixel(fx_p, fy_p, fz_p, fx, fy, cx_cam, cy_cam)
        if pred_pixel is not None:
            cv2.circle(frame_bgr, pred_pixel, 20, (0, 0, 255), 2)
            cv2.line(frame_bgr, history[-1], pred_pixel, (0, 0, 255), 2)
            cv2.putText(
                frame_bgr,
                f"+{PREDICTION_HORIZON}s",
                (pred_pixel[0] + 25, pred_pixel[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

    writer.write(frame_bgr)

writer.release()
cam.close()
print(f"\nSaved to {OUTPUT_PATH}")
