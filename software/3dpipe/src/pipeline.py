import cv2
import numpy as np
import pyzed.sl as sl
from ultralytics.models import YOLO

SPORTS_BALL_CLASS_ID = 32


def open_svo(path: str) -> sl.Camera:
    cam = sl.Camera()

    init_params = sl.InitParameters()
    init_params.set_from_svo_file(path)
    init_params.svo_real_time_mode = False
    init_params.coordinate_units = sl.UNIT.METER

    status = cam.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError(f"Could not open SVO2 file: {status}")

    return cam


def get_intrinsics(cam: sl.Camera) -> tuple[float, float, float, float]:
    calib = (
        cam.get_camera_information()
        .camera_configuration.calibration_parameters.left_cam
    )
    return calib.fx, calib.fy, calib.cx, calib.cy


def grab_frame(
    cam: sl.Camera,
    mat_rgb: sl.Mat,
    mat_xyz: sl.Mat,
) -> tuple[np.ndarray, np.ndarray] | None:
    status = cam.grab()
    if status == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
        return None
    if status != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError(f"Grab failed: {status}")

    cam.retrieve_image(mat_rgb, sl.VIEW.LEFT)
    cam.retrieve_measure(mat_xyz, sl.MEASURE.XYZ)

    # ZED outputs BGRA (4 channels), but YOLO expects RGB (3 channels)
    left_rgb = cv2.cvtColor(mat_rgb.get_data(), cv2.COLOR_BGRA2RGB)
    xyz_map = mat_xyz.get_data()

    return left_rgb, xyz_map


def object_3d_position(
    xyz_map: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    min_valid_points: int = 5,
) -> tuple[float, float, float] | None:
    patch = xyz_map[y1:y2, x1:x2, :3].reshape(-1, 3)
    valid = patch[np.isfinite(patch).all(axis=1)]
    if len(valid) < min_valid_points:
        return None
    
    return tuple(np.median(valid, axis=0).tolist())


def project_to_pixel(
    x: float, y: float, z: float,
    fx: float, fy: float, cx: float, cy: float,
) -> tuple[int, int] | None:
    if z <= 0:
        return None
    return int(fx * x / z + cx), int(fy * y / z + cy)


def load_model(weights: str = "yolov8x.pt") -> YOLO:
    return YOLO(weights)


def detect_ball_bbox(
    model: YOLO,
    left_rgb: np.ndarray,
    conf: float = 0.15,
    classes: list[int] | None = None,
) -> tuple[int, int, int, int] | None:
    if classes is None:
        classes = [SPORTS_BALL_CLASS_ID]
    results = model(left_rgb, conf=conf, classes=classes, verbose=False)

    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return None

    best = int(boxes.conf.argmax())
    x1, y1, x2, y2 = [int(v) for v in boxes.xyxy[best].tolist()]

    return x1, y1, x2, y2


class BallKalmanFilter:
    """ Tracks ball position and velocity in 3D using a Kalman filter.
    
    Each frame: call predict() to get a physics-based guess, then correct()
    with the camera measurement to get a smoothed result.
    
    State vector: [x, y, z, vx, vy, vz] - position and velocity.
    
    Only position is measured, velocity is inferred by the filter.
    """
    def __init__(self, dt: float) -> None:
        # 6 state variables (x, y, z, vx, vy, vz), 3 measurements (x, y, z)
        self.kf = cv2.KalmanFilter(6, 3)

        # Physics model: next_pos = pos + vel * dt, velocity is constant.
        self.kf.transitionMatrix = np.array([
            [1, 0, 0, dt, 0,  0 ],
            [0, 1, 0, 0,  dt, 0 ],
            [0, 0, 1, 0,  0,  dt],
            [0, 0, 0, 1,  0,  0 ],
            [0, 0, 0, 0,  1,  0 ],
            [0, 0, 0, 0,  0,  1 ],
        ], dtype=np.float32)

        # Only x, y, z are measured, they are extracted them from the 6-value state.
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
        ], dtype=np.float32)

        # Trust in the physics model. Lower value = more trust.
        # Velocity noise is higher because the ball can change speed unexpectedly.
        self.kf.processNoiseCov = np.diag(
            [0.0001, 0.0001, 0.0001, 0.01, 0.01, 0.01]
        ).astype(np.float32)

        # Noise in the camera measurements. Lower valur = more trust in the camera.
        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.001

        # errorCovPost is the uncertainty matrix. Setting it to identity (1s on diagonal)
        # makes the filter trust the first measurement heavily, before it has converged.
        self.kf.errorCovPost = np.eye(6, dtype=np.float32)
        self.initialized = False

    def reset(self, x: float, y: float, z: float) -> None:
        # Set starting position when ball is first detected, assume zero velocity.
        self.kf.statePost = np.array(
            [[x], [y], [z], [0], [0], [0]], dtype=np.float32
        )
        self.initialized = True

    def predict(self) -> tuple[float, float, float]:
        # Step the physics model forward one frame, returns predicted (x, y, z).
        state = self.kf.predict()
        return float(state[0, 0]), float(state[1, 0]), float(state[2, 0])

    def correct(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        # Feed in a camera measurement, filter blends it with the prediction.
        # Returns the smoothed (x, y, z).
        measurement = np.array([[x], [y], [z]], dtype=np.float32)
        state = self.kf.correct(measurement)
        return float(state[0, 0]), float(state[1, 0]), float(state[2, 0])

    def predict_ahead(self, t: float) -> tuple[float, float, float]:
        # Linear extrapolation: where will the ball be in t seconds?
        # Uses current position and velocity from the filter state.
        x = float(self.kf.statePost[0, 0])
        y = float(self.kf.statePost[1, 0])
        z = float(self.kf.statePost[2, 0])
        vx = float(self.kf.statePost[3, 0])
        vy = float(self.kf.statePost[4, 0])
        vz = float(self.kf.statePost[5, 0])
        return x + vx * t, y + vy * t, z + vz * t
