import argparse

import cv2
import pyzed.sl as sl


def build_model_map() -> dict:
    available = {}
    for name in dir(sl.OBJECT_DETECTION_MODEL):
        if not name.isupper():
            continue
        if name in {"LAST"}:
            continue
        available[name] = getattr(sl.OBJECT_DETECTION_MODEL, name)
    return available


MODEL_MAP = build_model_map()
DEFAULT_MODEL = (
    "MULTI_CLASS_BOX_FAST"
    if "MULTI_CLASS_BOX_FAST" in MODEL_MAP
    else next(iter(MODEL_MAP))
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ZED SDK object detection demo")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        choices=sorted(MODEL_MAP.keys()),
        help="Detection model to use",
    )
    parser.add_argument(
        "--confidence",
        type=int,
        default=25,
        help="Detection confidence threshold (0-100)",
    )
    parser.add_argument(
        "--no-tracking",
        action="store_true",
        help="Disable positional tracking and object tracking",
    )
    parser.add_argument(
        "--segmentation",
        action="store_true",
        help="Enable segmentation masks",
    )
    return parser.parse_args()


def enable_tracking_if_requested(
    zed: sl.Camera,
    detection_params: sl.ObjectDetectionParameters,
) -> bool:
    if not detection_params.enable_tracking:
        return True
    tracking_params = sl.PositionalTrackingParameters()
    status = zed.enable_positional_tracking(tracking_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"Failed to enable positional tracking: {status}")
        return False
    return True


def main() -> int:
    args = parse_args()

    zed = sl.Camera()
    init_params = sl.InitParameters()
    init_params.coordinate_units = sl.UNIT.METER

    status = zed.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"Failed to open ZED camera: {status}")
        return 1

    detection_params = sl.ObjectDetectionParameters()
    detection_params.enable_tracking = not args.no_tracking
    detection_params.enable_segmentation = args.segmentation
    detection_params.detection_model = MODEL_MAP[args.model]

    if not enable_tracking_if_requested(zed, detection_params):
        zed.close()
        return 1

    status = zed.enable_object_detection(detection_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"Failed to enable object detection: {status}")
        zed.close()
        return 1

    runtime_params = sl.RuntimeParameters()
    detection_params_rt = sl.ObjectDetectionRuntimeParameters()
    detection_params_rt.detection_confidence_threshold = args.confidence

    objects = sl.Objects()
    image = sl.Mat()

    print("Press q to quit")

    try:
        while True:
            if zed.grab(runtime_params) != sl.ERROR_CODE.SUCCESS:
                continue

            zed.retrieve_image(image, sl.VIEW.LEFT)
            zed.retrieve_objects(objects, detection_params_rt)

            frame = image.get_data().copy()

            for obj in objects.object_list:
                if detection_params.enable_tracking and obj.tracking_state != sl.OBJECT_TRACKING_STATE.OK:
                    continue

                bbox = obj.bounding_box_2d
                x_min = int(min(p[0] for p in bbox))
                y_min = int(min(p[1] for p in bbox))
                x_max = int(max(p[0] for p in bbox))
                y_max = int(max(p[1] for p in bbox))

                color = (0, 255, 0)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)

                pos = obj.position
                label = f"{obj.label.name} id:{obj.id} conf:{obj.confidence}% z:{pos[2]:.2f}m"
                cv2.putText(
                    frame,
                    label,
                    (x_min, max(0, y_min - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )

            cv2.imshow("ZED Object Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cv2.destroyAllWindows()
        zed.disable_object_detection()
        if detection_params.enable_tracking:
            zed.disable_positional_tracking()
        zed.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

