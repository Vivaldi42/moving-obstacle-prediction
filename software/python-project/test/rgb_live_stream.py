import cv2
import pyzed.sl as sl


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

    print("Streaming ZED video. Press q or Esc to stop.")

    try:
        while True:
            if zed.grab(runtime) != sl.ERROR_CODE.SUCCESS:
                continue

            zed.retrieve_image(left, sl.VIEW.LEFT)
            frame = left.get_data()
            bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            cv2.imshow("ZED Python Stream", bgr)
            key = cv2.waitKey(1)
            if key == ord("q") or key == 27:
                break
    finally:
        cv2.destroyAllWindows()
        zed.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

