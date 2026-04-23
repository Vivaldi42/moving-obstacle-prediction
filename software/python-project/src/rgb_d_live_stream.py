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
    left = sl.Mat()
    depth = sl.Mat()

    max_depth_m = 10.0
    overlay_alpha = 0.45
    window_name = "ZED RGB-D Overlay"
    print("Streaming aligned RGB-D overlay. Press q or Esc to stop.")

    try:
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

        def on_alpha_change(value: int) -> None:
            nonlocal overlay_alpha
            overlay_alpha = max(0, min(100, value)) / 100.0

        cv2.createTrackbar("Overlay %", window_name, int(overlay_alpha * 100), 100, on_alpha_change)

        while True:
            if zed.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                continue

            zed.retrieve_image(left, sl.VIEW.LEFT)
            zed.retrieve_measure(depth, sl.MEASURE.DEPTH)

            bgra = left.get_data()
            bgr = cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

            depth_map = depth.get_data()
            if depth_map.shape[:2] != rgb.shape[:2]:
                depth_map = cv2.resize(
                    depth_map,
                    (rgb.shape[1], rgb.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )

            rgbd = np.dstack((rgb, depth_map))
            _ = rgbd

            depth_color = depth_to_color(depth_map, max_depth_m)
            overlay = cv2.addWeighted(bgr, 1.0 - overlay_alpha, depth_color, overlay_alpha, 0.0)
            cv2.imshow(window_name, overlay)

            key = cv2.waitKey(1)
            if key == ord("q") or key == 27:
                break
    finally:
        cv2.destroyAllWindows()
        zed.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

