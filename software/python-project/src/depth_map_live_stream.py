import cv2
import numpy as np
import pyzed.sl as sl


def depth_to_color(depth_map: np.ndarray, max_depth_m: float) -> np.ndarray:
    depth = np.nan_to_num(depth_map, nan=max_depth_m, posinf=max_depth_m, neginf=0.0)
    depth = np.clip(depth, 0.0, max_depth_m)
    depth_normalized = (depth / max_depth_m * 255.0).astype(np.uint8)
    colored = cv2.applyColorMap(255 - depth_normalized, cv2.COLORMAP_JET)
    return colored


def main() -> int:
    zed = sl.Camera()

    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_units = sl.UNIT.METER

    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print(f"zed.open failed: {err}")
        return 1

    runtime = sl.RuntimeParameters()
    depth = sl.Mat()

    max_depth_m = 10.0
    print("Streaming ZED depth map. Press q or Esc to stop.")

    try:
        while True:
            if zed.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                continue

            zed.retrieve_measure(depth, sl.MEASURE.DEPTH)
            depth_map = depth.get_data()
            colored = depth_to_color(depth_map, max_depth_m)

            cv2.imshow("ZED Depth Map", colored)
            key = cv2.waitKey(1)
            if key == ord("q") or key == 27:
                break
    finally:
        cv2.destroyAllWindows()
        zed.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

