import os
import cv2
import numpy as np
import pyzed.sl as sl
from collections import deque
from pipeline import (
    open_svo, get_intrinsics, grab_frame,
    load_model, detect_ball_bbox, calc_ball_3d_position,
    project_to_pixel, BallKalmanFilter,
)

SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-34-15.svo2"
# SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_ball_up_a_ramp_and_back_21-45-51.svo2"
OUTPUT_PATH = "/app/output/output.mp4"
FPS = 30
PREDICTION_HORIZON = 0.2
MAX_MISSED = 5

# --- setup ---

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

cam = open_svo(SVO_PATH)
fx, fy, cx_cam, cy_cam = get_intrinsics(cam)
model = load_model("yolov8x.pt")
kf = BallKalmanFilter(dt=1 / FPS)

mat_rgb = sl.Mat()
mat_xyz = sl.Mat()

writer = cv2.VideoWriter(
    OUTPUT_PATH,
    cv2.VideoWriter.fourcc(*"mp4v"),
    FPS,
    (1920, 1080),
)

trail = deque()
pred_trail = deque()
pred_buffer = {}
missed = 0
corrections = 0
frame_idx = 0


while True:
    result = grab_frame(cam, mat_rgb, mat_xyz)
    if result is None:
        break

    left_rgb, xyz_map = result
    frame_bgr = cv2.cvtColor(left_rgb, cv2.COLOR_RGB2BGR)

    if kf.initialized:
        kf.predict()

    detection = detect_ball_bbox(model, left_rgb)
    current_pixel = None

    if detection is not None:
        x1, y1, x2, y2 = detection
        xyz = calc_ball_3d_position(xyz_map, x1, y1, x2, y2)
        if xyz is not None:
            x, y, z = xyz
            if not kf.initialized:
                kf.reset(x, y, z)
                kf.predict()
            x, y, z = kf.correct(x, y, z)
            current_pixel = project_to_pixel(x, y, z, fx, fy, cx_cam, cy_cam)
            missed = 0
            corrections += 1
    else:
        missed += 1

    # coast on KF when detection is lost
    if kf.initialized and missed > 0 and missed < MAX_MISSED:
        px, py, pz = kf.predict()
        current_pixel = project_to_pixel(px, py, pz, fx, fy, cx_cam, cy_cam)

    if current_pixel is not None:
        trail.append(current_pixel)

    # draw trail
    for i in range(1, len(trail)):
        cv2.line(frame_bgr, trail[i - 1], trail[i], (0, 255, 0), 2)

    # draw current position
    if current_pixel is not None:
        color = (0, 255, 0) if missed == 0 else (0, 165, 255)
        cv2.circle(frame_bgr, current_pixel, 15, color, 3)
        if kf.initialized:
            cx, cy, cz = (
                float(kf.kf.statePost[0, 0]),
                float(kf.kf.statePost[1, 0]),
                float(kf.kf.statePost[2, 0]),
            )
            label = f"x:{cx:.2f} y:{cy:.2f} z:{cz:.2f}m"
            cv2.putText(
                frame_bgr, label,
                (current_pixel[0] + 20, current_pixel[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
            )

    # draw predicted position
    if corrections >= 2 and missed < MAX_MISSED:
        px, py, pz = kf.predict_ahead(PREDICTION_HORIZON)
        target_frame = frame_idx + round(PREDICTION_HORIZON * FPS)
        pred_buffer[target_frame] = (px, py, pz)
        pred_pixel = project_to_pixel(px, py, pz, fx, fy, cx_cam, cy_cam)
        if pred_pixel is not None:
            pred_trail.append(pred_pixel)
            for i in range(1, len(pred_trail)):
                cv2.line(frame_bgr, pred_trail[i - 1], pred_trail[i], (0, 0, 255), 2)
            cv2.circle(frame_bgr, pred_pixel, 15, (0, 0, 255), 3)
            if current_pixel is not None:
                cv2.line(frame_bgr, current_pixel, pred_pixel, (0, 0, 255), 2)
            pred_label = f"x:{px:.2f} y:{py:.2f} z:{pz:.2f}m +{PREDICTION_HORIZON}s"
            cv2.putText(
                frame_bgr, pred_label,
                (pred_pixel[0] + 20, pred_pixel[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
            )

    # compare past prediction to actual position and show error with color coding
    if frame_idx in pred_buffer and kf.initialized and current_pixel is not None:
        px, py, pz = pred_buffer.pop(frame_idx)
        ax = float(kf.kf.statePost[0, 0])
        ay = float(kf.kf.statePost[1, 0])
        az = float(kf.kf.statePost[2, 0])
        error = float(np.linalg.norm([px - ax, py - ay, pz - az]))

        if error < 0.02:
            acc_color = (0, 255, 0)      # green  - < 2 cm
        elif error < 0.06:
            acc_color = (0, 255, 255)    # yellow - 2-6 cm
        else:
            acc_color = (0, 0, 255)      # red    - > 6 cm

        cv2.circle(frame_bgr, current_pixel, 25, acc_color, 4)
        cv2.putText(
            frame_bgr, f"err:{error * 100:.1f}cm",
            (current_pixel[0] + 20, current_pixel[1] - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, acc_color, 2,
        )

    writer.write(frame_bgr)
    frame_idx += 1

# --- cleanup ---

writer.release()
cam.close()
print(f"Saved to {OUTPUT_PATH}")
