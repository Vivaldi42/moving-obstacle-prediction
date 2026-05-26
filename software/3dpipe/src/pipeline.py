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
) -> tuple[float, float, float] | None:
    patch = xyz_map[y1:y2, x1:x2, :3].reshape(-1, 3)
    valid = patch[np.isfinite(patch).all(axis=1)]
    return tuple(np.median(valid, axis=0).tolist()) if len(valid) else None


def project_to_pixel(
    x: float, y: float, z: float,
    fx: float, fy: float, cx: float, cy: float,
) -> tuple[int, int] | None:
    if z <= 0:
        return None
    return int(fx * x / z + cx), int(fy * y / z + cy)


def load_model(weights: str = "yolov8x.pt") -> YOLO:
    return YOLO(weights)


def detect(
    model: YOLO,
    left_rgb: np.ndarray,
) -> tuple[int, int, int, int] | None:
    results = model(left_rgb, conf=0.25, classes=[SPORTS_BALL_CLASS_ID], verbose=False)

    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return None

    best = int(boxes.conf.argmax())
    x1, y1, x2, y2 = [int(v) for v in boxes.xyxy[best].tolist()]

    return x1, y1, x2, y2


class BallKalmanFilter:

    def __init__(self, dt: float) -> None:
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

        self.kf.processNoiseCov = np.diag(
            [0.0001, 0.0001, 0.0001, 0.01, 0.01, 0.01]
        ).astype(np.float32)

        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.001

        self.kf.errorCovPost = np.eye(6, dtype=np.float32)
        self.initialized = False

    def init(self, x: float, y: float, z: float) -> None:
        self.kf.statePost = np.array(
            [[x], [y], [z], [0], [0], [0]], dtype=np.float32
        )
        self.initialized = True

    def predict(self) -> tuple[float, float, float]:
        state = self.kf.predict()
        return float(state[0]), float(state[1]), float(state[2])

    def correct(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        measurement = np.array([[x], [y], [z]], dtype=np.float32)
        state = self.kf.correct(measurement)
        return float(state[0]), float(state[1]), float(state[2])

    def predict_ahead(self, t: float) -> tuple[float, float, float]:
        x = float(self.kf.statePost[0])
        y = float(self.kf.statePost[1])
        z = float(self.kf.statePost[2])
        vx = float(self.kf.statePost[3])
        vy = float(self.kf.statePost[4])
        vz = float(self.kf.statePost[5])
        return x + vx * t, y + vy * t, z + vz * t
