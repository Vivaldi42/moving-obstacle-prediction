import cv2
import numpy as np
import pyzed.sl as sl


def set_runtime_option(runtime: sl.RuntimeParameters, name: str, value: object) -> bool:
    if not hasattr(runtime, name):
        return False

    setattr(runtime, name, value)
    return True


def position_distance_m(
    position_a: tuple[float, float, float],
    position_b: tuple[float, float, float],
) -> float:
    return float(np.linalg.norm(np.array(position_a) - np.array(position_b)))


def median_depth_in_ball(
    depth_map: np.ndarray,
    ball_mask: np.ndarray,
    cx: int,
    cy: int,
    radius: int,
) -> float | None:
    # Depth can be invalid at a single pixel, especially on small low-texture objects.
    sample_radius = max(10, min(int(radius * 1.5), 45))
    y_min = max(0, cy - sample_radius)
    y_max = min(depth_map.shape[0], cy + sample_radius + 1)
    x_min = max(0, cx - sample_radius)
    x_max = min(depth_map.shape[1], cx + sample_radius + 1)

    depth_roi = depth_map[y_min:y_max, x_min:x_max]
    mask_roi = ball_mask[y_min:y_max, x_min:x_max]

    yy, xx = np.ogrid[y_min:y_max, x_min:x_max]
    circle_roi = (xx - cx) ** 2 + (yy - cy) ** 2 <= sample_radius**2
    valid_depth = np.isfinite(depth_roi) & (depth_roi > 0.0)

    valid_depths = depth_roi[(mask_roi > 0) & circle_roi & valid_depth]
    if valid_depths.size < 6:
        valid_depths = depth_roi[circle_roi & valid_depth]

    if valid_depths.size < 6:
        return None

    # A tennis ball is usually the closest object inside this ROI; use a low percentile
    # to avoid the background dominating when the ball itself has sparse depth.
    return float(np.percentile(valid_depths, 25))


def main() -> int:
    # Open the ZED camera and request metric depth values.
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
    set_runtime_option(runtime, "confidence_threshold", 100)
    set_runtime_option(runtime, "texture_confidence_threshold", 100)
    set_runtime_option(runtime, "enable_fill_mode", True)
    left = sl.Mat()
    depth = sl.Mat()

    # Read left-camera intrinsics for pinhole projection from pixel + depth to XYZ.
    camera_info = zed.get_camera_information()
    left_cam = camera_info.camera_configuration.calibration_parameters.left_cam
    fx = left_cam.fx
    fy = left_cam.fy
    cx_principal = left_cam.cx
    cy_principal = left_cam.cy

    # Tennis-ball HSV range: yellow-green, tuned as a starting point.
    lower_tennis = np.array([25, 80, 80], dtype=np.uint8)
    upper_tennis = np.array([45, 255, 255], dtype=np.uint8)
    min_area_px = 500
    last_position: tuple[float, float, float] | None = None
    displayed_position: tuple[float, float, float] | None = None
    last_position_age = 0
    max_hold_frames = 30
    display_deadband_m = 0.01

    print("Detecting tennis ball. Press q or Esc to stop.")

    try:
        while True:
            # Grab a synchronized camera frame.
            if zed.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                continue

            # Retrieve the left RGB image and aligned depth map.
            zed.retrieve_image(left, sl.VIEW.LEFT)
            zed.retrieve_measure(depth, sl.MEASURE.DEPTH)

            bgra = left.get_data()
            rgb = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGB)
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            depth_map = depth.get_data()

            # Convert RGB to HSV and isolate yellow-green tennis-ball pixels.
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
            mask = cv2.inRange(hsv, lower_tennis, upper_tennis)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # Find candidate blobs and keep the largest contour above the area threshold.
            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            valid_contours = [
                contour for contour in contours if cv2.contourArea(contour) > min_area_px
            ]

            if valid_contours:
                ball_contour = max(valid_contours, key=cv2.contourArea)
                (x, y), radius = cv2.minEnclosingCircle(ball_contour)
                cx = int(round(x))
                cy = int(round(y))
                radius = int(round(radius))

                if 0 <= cy < depth_map.shape[0] and 0 <= cx < depth_map.shape[1]:
                    z_m = median_depth_in_ball(depth_map, mask, cx, cy, radius)

                    if z_m is not None:
                        # Convert pixel center and depth to camera-frame 3D coordinates.
                        x_m = (cx - cx_principal) * z_m / fx
                        y_m = (cy - cy_principal) * z_m / fy
                        last_position = (x_m, y_m, z_m)
                        last_position_age = 0

                        if (
                            displayed_position is None
                            or position_distance_m(last_position, displayed_position)
                            >= display_deadband_m
                        ):
                            displayed_position = last_position

                        display_x, display_y, display_z = displayed_position
                        print(
                            "Ball position: "
                            f"X={display_x:.3f} m, "
                            f"Y={display_y:.3f} m, "
                            f"Z={display_z:.3f} m"
                        )

                        label = f"X:{display_x:.2f} Y:{display_y:.2f} Z:{display_z:.2f} m"
                    elif last_position is not None and last_position_age < max_hold_frames:
                        last_position_age += 1
                        display_x, display_y, display_z = displayed_position or last_position
                        label = (
                            f"held X:{display_x:.2f} "
                            f"Y:{display_y:.2f} "
                            f"Z:{display_z:.2f} m"
                        )
                        print(
                            "Ball position held: "
                            f"X={display_x:.3f} m, "
                            f"Y={display_y:.3f} m, "
                            f"Z={display_z:.3f} m"
                        )
                    else:
                        label = "Depth unavailable"

                    # Draw the enclosing circle, center point, and current position label.
                    cv2.circle(bgr, (cx, cy), radius, (0, 255, 255), 2)
                    cv2.circle(bgr, (cx, cy), 4, (0, 0, 255), -1)
                    cv2.putText(
                        bgr,
                        label,
                        (max(0, cx - radius), max(20, cy - radius - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )

            # Display both the binary mask and the annotated RGB camera image.
            cv2.imshow("Tennis Ball HSV Mask", mask)
            cv2.imshow("ZED Tennis Ball 3D Position", bgr)

            key = cv2.waitKey(1)
            if key == ord("q") or key == 27:
                break
    finally:
        cv2.destroyAllWindows()
        zed.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
