"""
Captures paired left-RGB and depth images from a live ZED camera.

Press ENTER to save a frame, Q+ENTER to quit.
Each capture saves:
  cap_NNN_left.png   - 1280x720 RGB (left camera)
  cap_NNN_depth.npy  - 1280x720 float32 depth in metres

On first capture, also writes intrinsics.json.
"""

import json
import os

import cv2
import numpy as np
import pyzed.sl as sl

OUTPUT_DIR = "/datasets/Dataset_2/Clean/Detection_Accuracy"


def next_index(folder: str) -> int:
    existing = [f for f in os.listdir(folder) if f.startswith("cap_") and f.endswith("_left.png")]
    return len(existing) + 1


def save_intrinsics(cam: sl.Camera, folder: str) -> None:
    path = os.path.join(folder, "intrinsics.json")
    if os.path.exists(path):
        return
    calib = cam.get_camera_information().camera_configuration.calibration_parameters.left_cam
    with open(path, "w") as f:
        json.dump({"fx": calib.fx, "fy": calib.fy, "cx": calib.cx, "cy": calib.cy}, f, indent=2)
    print(f"Saved intrinsics -> {path}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cam = sl.Camera()
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD1080
    init_params.coordinate_units = sl.UNIT.METER
    init_params.depth_mode = sl.DEPTH_MODE.NEURAL

    status = cam.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError(f"Could not open camera: {status}")

    save_intrinsics(cam, OUTPUT_DIR)

    mat_rgb = sl.Mat()
    mat_depth = sl.Mat()
    runtime_params = sl.RuntimeParameters()

    i = next_index(OUTPUT_DIR)
    print(f"Starting at capture index {i}.")
    print("ENTER = capture | Q+ENTER = quit")

    while True:
        user_input = input("> ").strip().lower()

        if user_input == "q":
            break

        # Grab the freshest frame before saving
        for _ in range(5):
            cam.grab(runtime_params)

        cam.retrieve_image(mat_rgb, sl.VIEW.LEFT)
        cam.retrieve_measure(mat_depth, sl.MEASURE.DEPTH)

        frame_bgr = cv2.cvtColor(mat_rgb.get_data(), cv2.COLOR_BGRA2BGR)
        depth = mat_depth.get_data().squeeze()  # (H, W) float32, metres

        name = f"cap_{i:03d}"
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"{name}_left.png"), frame_bgr)
        np.save(os.path.join(OUTPUT_DIR, f"{name}_depth.npy"), depth)
        print(f"Saved {name}")
        i += 1

    cam.close()


if __name__ == "__main__":
    main()
