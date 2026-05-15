import cv2
import pyzed.sl as sl
import numpy as np
from typing import Optional, Tuple
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


def grab_frame(cam: sl.Camera, mat_rgb: sl.Mat) -> Optional[np.ndarray]:
    status = cam.grab()
    if status == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
        return None
    if status != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError(f"grab failed: {status}")
    
    cam.retrieve_image(mat_rgb, sl.VIEW.LEFT)
    
    return cv2.cvtColor(mat_rgb.get_data(), cv2.COLOR_BGRA2RGB)


def load_model(weights: str = "yolov8x.pt") -> YOLO:
    return YOLO(weights)


def detect(model: YOLO, left_rgb: np.ndarray) -> Optional[Tuple[int, int]]:
    results = model(left_rgb, conf=0.25, classes=[SPORTS_BALL_CLASS_ID], verbose=False)
    
    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return None
    
    best = int(boxes.conf.argmax())
    x1, y1, x2, y2 = boxes.xyxy[best].tolist()
    
    return int((x1 + x2) / 2), int((y1 + y2) / 2)
