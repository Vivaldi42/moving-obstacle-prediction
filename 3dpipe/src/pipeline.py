import cv2
import numpy as np
import pyzed.sl as sl
from dataclasses import dataclass
from ultralytics.models import YOLO

SPORTS_BALL_CLASS_ID = 32


@dataclass
class KFConfig:
    name: str
    # How much the filter allows velocity to change per frame.
    # Higher = adapts faster to acceleration, lower = smoother but lags on speed changes.
    velocity_process_noise: float = 0.01
    # Camera measurement noise per axis (variance in m²).
    # From ZED static analysis: X std=0.8cm, Y std=1.1cm, Z std=0.8cm.
    measurement_noise_x: float = 0.001
    measurement_noise_y: float = 0.001
    measurement_noise_z: float = 0.001


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


def calc_ball_3d_position(
    xyz_map: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    min_valid_points: int = 5,
    front_tolerance_m: float = 0.005,
) -> tuple[float, float, float] | None:
    # xyz_map: (H, W, 3) dense point cloud from sl.MEASURE.XYZ - each pixel (u,v)
    #   holds a pre-computed (X, Y, Z) in metres in camera frame.
    # x1,y1,x2,y2: YOLO bounding box in pixels.
    # Returns (X, Y, Z) of the object's front-face centroid:
    #   1. Extract all valid depth pixels inside the bbox.
    #   2. Keep only those within front_tolerance_m of the minimum depth (the front face).
    #   3. Use their pixel centroid as (u, v) and median Z as depth.
    #   This corrects for floor/surface occlusion of the object's bottom, which shifts
    #   the naive bbox-center upward and could give a wrong Y reading.
    #   Returns None if fewer than min_valid_points finite points exist in the bbox.
    h, w = xyz_map.shape[:2]
    bbox_patch = xyz_map[
        max(0, y1):min(h, y2 + 1),
        max(0, x1):min(w, x2 + 1),
        :3,
    ]

    ys, xs = np.meshgrid(
        np.arange(max(0, y1), min(h, y2 + 1)),
        np.arange(max(0, x1), min(w, x2 + 1)),
        indexing="ij",
    )

    z_patch = bbox_patch[:, :, 2]
    valid_mask = np.isfinite(z_patch) & (z_patch > 0)
    if valid_mask.sum() < min_valid_points:
        return None

    min_z = z_patch[valid_mask].min()
    front_mask = valid_mask & (z_patch <= min_z + front_tolerance_m)

    u = float(xs[front_mask].mean())
    v = float(ys[front_mask].mean())
    z = float(np.median(z_patch[front_mask]))

    xyz_at_centroid = xyz_map[int(round(v)), int(round(u))]
    if not np.isfinite(xyz_at_centroid).all():
        return None

    return float(xyz_at_centroid[0]), float(xyz_at_centroid[1]), z


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
    def __init__(self, dt: float, config: KFConfig | None = None) -> None:
        if config is None:
            config = KFConfig(name="default")

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

        # Observation matrix H. Only x, y, z are measured, they are extracted from the 6-value state.
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
        ], dtype=np.float32)

        vpn = config.velocity_process_noise
        self.kf.processNoiseCov = np.diag(
            [0.0001, 0.0001, 0.0001, vpn, vpn, vpn]
        ).astype(np.float32)

        self.kf.measurementNoiseCov = np.diag(
            [config.measurement_noise_x, config.measurement_noise_y, config.measurement_noise_z]
        ).astype(np.float32)

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

    def get_position(self) -> tuple[float, float, float]:
        return (
            float(self.kf.statePost[0, 0]),
            float(self.kf.statePost[1, 0]),
            float(self.kf.statePost[2, 0]),
        )

    def predict_ahead(self, t: float) -> tuple[float, float, float]:
        # Linear extrapolation: where will the ball be in t seconds?
        # Uses current position and velocity from the filter state.
        x, y, z = self.get_position()
        vx = float(self.kf.statePost[3, 0])
        vy = float(self.kf.statePost[4, 0])
        vz = float(self.kf.statePost[5, 0])
        return x + vx * t, y + vy * t, z + vz * t

# Cons
# no gravity or acceleration taken into account
# Constant-velocity Kalman filter. Bounces, spins or curved trajectories will cause lag.

# Problem with ground truth
# gt is built from the same YOLO + ZED pipeline that drives the predictions - not from an independent source.
# YOLO bbox bias affects both the prediction inputs and the future "ground truth" frame in the same direction, so systematic offsets cancel out in the FDE calculation.
# ZED depth noise has consistent spatial patterns - the filter absorbs them, and the "ground truth" carries them too, so they partially cancel again.
# The KF was corrected every frame with raw measurements, so its predictions are essentially a smoothed version of those measurements projected forward. Comparing that to a future raw measurement from the same source is an easy test.
# A real error of e.g. 5 cm could report as ~0 if both the prediction and "ground truth" share the same 5 cm bias.
# Fix: manually annotate ball positions on a sample of frames, or evaluate on a separate recording that was never used to tune the filter's noise covariances.

        # # Measurement noise accounts for ZED depth noise (from static experiment: X=0.9cm, Y=1.2cm, Z=0.8cm)
        # # plus YOLO bbox jitter on a moving ball. Values are higher than pure ZED variance floor.
        # self.kf.measurementNoiseCov = np.diag(
        #     [0.0003, 0.0004, 0.0003]
        # ).astype(np.float32)