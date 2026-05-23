import cv2
import pyzed.sl as sl
import numpy as np
from ultralytics.models import YOLO


SPORTS_BALL_CLASS_ID = 32
DEPTH_PATCH_RADIUS = 4


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
    calib = cam.get_camera_information().camera_configuration.calibration_parameters.left_cam
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
        raise RuntimeError(f"grab failed: {status}")

    cam.retrieve_image(mat_rgb, sl.VIEW.LEFT)
    cam.retrieve_measure(mat_xyz, sl.MEASURE.XYZ)

    left_rgb = cv2.cvtColor(mat_rgb.get_data(), cv2.COLOR_BGRA2RGB)
    xyz_map = mat_xyz.get_data()

    return left_rgb, xyz_map

def resolve_xyz(
    xyz_map: np.ndarray,
    cx: int,
    cy: int,
) -> tuple[float, float, float] | None:
    x, y, z, _ = xyz_map[cy, cx]
    if np.isfinite(x) and np.isfinite(y) and np.isfinite(z):
        return float(x), float(y), float(z)

    h, w = xyz_map.shape[:2]
    r = DEPTH_PATCH_RADIUS
    patch = xyz_map[
        max(0, cy - r):min(h, cy + r + 1),
        max(0, cx - r):min(w, cx + r + 1),
        :3,
    ]
    pts = patch.reshape(-1, 3)
    valid = pts[np.all(np.isfinite(pts), axis=1)]
    if len(valid) == 0:
        return None

    return tuple(np.median(valid, axis=0).tolist())

def project_to_pixel(
    x: float,
    y: float,
    z: float,
    fx: float,
    fy: float,
    cx: float,
    cy: float,
) -> tuple[int, int] | None:
    if z <= 0:
        return None
    return int(fx * x / z + cx), int(fy * y / z + cy)


def load_model(weights: str = "yolov8x.pt") -> YOLO:
    return YOLO(weights)


def detect(
    model: YOLO,
    left_rgb: np.ndarray,
    classes: list[int] | None = None,
) -> tuple[int, int] | None:
    if classes is None:
        classes = [SPORTS_BALL_CLASS_ID]

    results = model(left_rgb, conf=0.25, classes=classes, verbose=False)

    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return None

    best = int(boxes.conf.argmax())
    x1, y1, x2, y2 = boxes.xyxy[best].tolist()

    return int((x1 + x2) / 2), int((y1 + y2) / 2)

class BallKalmanFilter:
    """Constant-velocity Kalman filter in 3D metres. State: [x, y, z, vx, vy, vz]."""

    def __init__(self, dt: float = 1 / 30) -> None:
        self.kf = cv2.KalmanFilter(6, 3)

        self.kf.transitionMatrix = np.array([
            [1, 0, 0, dt, 0,  0 ],
            [0, 1, 0, 0,  dt, 0 ],
            [0, 0, 1, 0,  0,  dt],
            [0, 0, 0, 1,  0,  0 ],
            [0, 0, 0, 0,  1,  0 ],
            [0, 0, 0, 0,  0,  1 ],
        ], dtype=np.float32)

        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
        ], dtype=np.float32)

        # Position uncertainty low, velocity higher — ball moves smoothly
        self.kf.processNoiseCov = np.diag(
            [1e-4, 1e-4, 1e-4, 1e-2, 1e-2, 1e-2]
        ).astype(np.float32)

        # ZED depth noise ~1-2 cm
        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 1e-3

        self.kf.errorCovPost = np.eye(6, dtype=np.float32)
        self.initialized = False

    def init(self, x: float, y: float, z: float) -> None:
        self.kf.statePost = np.array(
            [[x], [y], [z], [0], [0], [0]], dtype=np.float32
        )
        self.initialized = True

    def predict(self) -> tuple[float, float, float]:
        state = self.kf.predict()
        return float(state[0, 0]), float(state[1, 0]), float(state[2, 0])

    def correct(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        measurement = np.array([[x], [y], [z]], dtype=np.float32)
        state = self.kf.correct(measurement)
        return float(state[0, 0]), float(state[1, 0]), float(state[2, 0])

    def predict_ahead(self, horizon: float) -> tuple[float, float, float]:
        state = self.kf.statePost
        x = float(state[0, 0])
        y = float(state[1, 0])
        z = float(state[2, 0])
        vx = float(state[3, 0])
        vy = float(state[4, 0])
        vz = float(state[5, 0])
        return x + vx * horizon, y + vy * horizon, z + vz * horizon
