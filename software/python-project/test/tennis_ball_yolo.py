import cv2
import numpy as np
import pyzed.sl as sl
from filterpy.kalman import KalmanFilter
from ultralytics import YOLO


COCO_BALL_CLASS = 32
N_PREDICT = 10
PATCH_SIZE = 5
CONFIDENCE_THRESHOLD = 0.5
DT = 1 / 30
MODEL_PATH = "yolo26n.pt"
WINDOW_NAME = "ZED + YOLO26"


def init_kalman() -> KalmanFilter:
    kf = KalmanFilter(dim_x=6, dim_z=3)
    kf.F = np.array(
        [
            [1.0, 0.0, 0.0, DT, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, DT, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, DT],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    kf.H = np.array(
        [
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    kf.R = np.eye(3, dtype=np.float64) * 0.05
    kf.Q = np.eye(6, dtype=np.float64) * 0.01
    kf.P = np.eye(6, dtype=np.float64) * 1.0
    kf.x = np.zeros((6, 1), dtype=np.float64)
    return kf


def get_3d_position(
    depth_map: np.ndarray,
    cx: int,
    cy: int,
    params: sl.CameraParameters,
) -> tuple[float, float, float] | None:
    half_patch = PATCH_SIZE // 2
    x_min = max(0, cx - half_patch)
    x_max = min(depth_map.shape[1], cx + half_patch + 1)
    y_min = max(0, cy - half_patch)
    y_max = min(depth_map.shape[0], cy + half_patch + 1)

    patch = depth_map[y_min:y_max, x_min:x_max]
    valid_depths = patch[np.isfinite(patch)]
    if valid_depths.size == 0:
        return None

    z_m = float(np.mean(valid_depths))
    if z_m <= 0.0:
        return None

    x_m = (cx - params.cx) * z_m / params.fx
    y_m = (cy - params.cy) * z_m / params.fy
    return x_m, y_m, z_m


def predict_trajectory(
    kf: KalmanFilter,
    dt: float,
    n_steps: int,
) -> list[tuple[float, float, float]]:
    x, y, z, vx, vy, vz = kf.x.flatten()
    trajectory = []
    for step in range(1, n_steps + 1):
        horizon = dt * step
        trajectory.append(
            (
                float(x + vx * horizon),
                float(y + vy * horizon),
                float(z + vz * horizon),
            )
        )
    return trajectory


def main() -> int:
    # SETUP
    zed = sl.Camera()

    init_params = sl.InitParameters()
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_units = sl.UNIT.METER

    status = zed.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"Failed to open ZED camera: {status}")
        return 1

    tracking_params = sl.PositionalTrackingParameters()
    status = zed.enable_positional_tracking(tracking_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"Failed to enable positional tracking: {status}")
        zed.close()
        return 1

    model = YOLO(MODEL_PATH)
    kf = init_kalman()
    kalman_initialized = False

    runtime = sl.RuntimeParameters()
    left_image = sl.Mat()
    depth_measure = sl.Mat()

    params = zed.get_camera_information().camera_configuration.calibration_parameters.left_cam
    frame_index = 0

    print("Running tennis ball tracking. Press q to stop.")

    try:
        while True:
            if zed.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                continue

            frame_index += 1

            zed.retrieve_image(left_image, sl.VIEW.LEFT)
            zed.retrieve_measure(depth_measure, sl.MEASURE.DEPTH)

            frame_bgra = left_image.get_data()
            frame_bgr = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
            depth_map = depth_measure.get_data()

            # DETECTION
            results = model(frame_bgr, verbose=False)
            best_detection = None
            best_confidence = -1.0

            if results:
                boxes = results[0].boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls.item())
                        confidence = float(box.conf.item())
                        if cls_id != COCO_BALL_CLASS or confidence < CONFIDENCE_THRESHOLD:
                            continue
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_detection = box

            detected_center = None
            measured_xyz = None
            trajectory = []

            if best_detection is not None:
                xyxy = best_detection.xyxy[0].detach().cpu().numpy()
                x1, y1, x2, y2 = xyxy.astype(int)
                cx = int(round((x1 + x2) / 2.0))
                cy = int(round((y1 + y2) / 2.0))
                cx = int(np.clip(cx, 0, frame_bgr.shape[1] - 1))
                cy = int(np.clip(cy, 0, frame_bgr.shape[0] - 1))
                detected_center = (cx, cy)

                # 3D EXTRACTION
                measured_xyz = get_3d_position(depth_map, cx, cy, params)

                # VISUALIZATION
                cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame_bgr,
                    f"tennis ball conf={best_confidence:.2f}",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                cv2.circle(frame_bgr, (cx, cy), 5, (0, 0, 255), -1)

            # KALMAN
            if measured_xyz is not None:
                measurement = np.array(measured_xyz, dtype=np.float64).reshape(3, 1)
                if not kalman_initialized:
                    kf.x[:3] = measurement
                    kf.x[3:] = 0.0
                    kalman_initialized = True
                else:
                    kf.predict()
                    kf.update(measurement)

                # PREDICTION
                trajectory = predict_trajectory(kf, DT, N_PREDICT)
                px, py, pz = trajectory[-1]
                x, y, z, vx, vy, vz = kf.x.flatten()
                print(
                    f"Frame {frame_index} | "
                    f"XYZ: ({x:.3f}, {y:.3f}, {z:.3f}) | "
                    f"Vel: ({vx:.3f}, {vy:.3f}, {vz:.3f}) | "
                    f"Pred+10: ({px:.3f}, {py:.3f}, {pz:.3f})"
                )
            elif kalman_initialized:
                kf.predict()
                trajectory = predict_trajectory(kf, DT, N_PREDICT)

            if detected_center is None and kalman_initialized:
                x, y, z = kf.x[:3].flatten()
                cv2.putText(
                    frame_bgr,
                    f"Predicted XYZ: ({x:.2f}, {y:.2f}, {z:.2f}) m",
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

            # VISUALIZATION
            cv2.imshow(WINDOW_NAME, frame_bgr)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        cv2.destroyAllWindows()
        zed.disable_positional_tracking()
        zed.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
