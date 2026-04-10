import sys
import pyzed.sl as sl
import cv2


def main():
    zed = sl.Camera()

    init_params = sl.InitParameters()
    init_params.coordinate_units = sl.UNIT.METER

    if zed.open(init_params) != sl.ERROR_CODE.SUCCESS:
        print("Failed to open ZED camera")
        sys.exit(1)

    tracking_params = sl.PositionalTrackingParameters()
    zed.enable_positional_tracking(tracking_params)

    obj_params = sl.ObjectDetectionParameters()
    obj_params.enable_tracking = True
    if zed.enable_object_detection(obj_params) != sl.ERROR_CODE.SUCCESS:
        print("Failed to enable object detection")
        zed.close()
        sys.exit(1)

    runtime_params = sl.RuntimeParameters()
    obj_runtime_params = sl.ObjectDetectionRuntimeParameters()
    objects = sl.Objects()
    image = sl.Mat()

    while True:
        if zed.grab(runtime_params) != sl.ERROR_CODE.SUCCESS:
            continue

        zed.retrieve_image(image, sl.VIEW.LEFT)
        zed.retrieve_objects(objects, obj_runtime_params)

        frame = image.get_data().copy()
        for obj in objects.object_list:
            if obj.tracking_state != sl.OBJECT_TRACKING_STATE.OK:
                continue

            pos = obj.position
            vel = obj.velocity
            state = [obj.id, pos[0], pos[1], pos[2], vel[0], vel[1], vel[2]]
            print(state)

            bbox = obj.bounding_box_2d
            x_min = int(min(p[0] for p in bbox))
            y_min = int(min(p[1] for p in bbox))
            x_max = int(max(p[0] for p in bbox))
            y_max = int(max(p[1] for p in bbox))
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            label = f"id:{obj.id} x:{pos[0]:.2f} y:{pos[1]:.2f} z:{pos[2]:.2f}"
            vel_label = f"vx:{vel[0]:.2f} vy:{vel[1]:.2f} vz:{vel[2]:.2f}"
            cv2.putText(frame, label, (x_min, max(0, y_min - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(frame, vel_label, (x_min, min(frame.shape[0] - 5, y_min + 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imshow("ZED Object States", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
    zed.close()


if __name__ == "__main__":
    main()
