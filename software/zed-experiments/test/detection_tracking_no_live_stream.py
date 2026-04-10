import sys
import pyzed.sl as sl


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

    while True:
        if zed.grab(runtime_params) != sl.ERROR_CODE.SUCCESS:
            continue

        zed.retrieve_objects(objects, obj_runtime_params)

        for obj in objects.object_list:
            if obj.tracking_state != sl.OBJECT_TRACKING_STATE.OK:
                continue

            pos = obj.position
            vel = obj.velocity
            state = [obj.id, pos[0], pos[1], pos[2], vel[0], vel[1], vel[2]]
            print(state)


if __name__ == "__main__":
    main()
