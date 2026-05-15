import json
import sys
import numpy as np
import pyzed.sl as sl

SVO_PATH = "/home/vladi/Documents/ZED/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2"
OUT_PATH = "svo2_contents.json"


def _open(path: str) -> sl.Camera:
    cam = sl.Camera()
    init = sl.InitParameters()
    init.set_from_svo_file(path)
    init.svo_real_time_mode = False
    init.depth_mode = sl.DEPTH_MODE.NONE  # don't compute depth — not stored
    if cam.open(init) != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError(f"Failed to open: {path}")
    return cam


def _sensor_entry(params) -> dict:
    return {
        "available": params.is_available,
        "rate_hz": params.sampling_rate if params.is_available else None,
    }


def schema_svo2(path: str) -> None:
    cam = _open(path)
    info = cam.get_camera_information()
    cfg  = info.camera_configuration
    cal  = cfg.calibration_parameters
    lc, rc = cal.left_cam, cal.right_cam
    sc   = info.sensors_configuration

    runtime = sl.RuntimeParameters()
    cam.grab(runtime)
    mat = sl.Mat()
    cam.retrieve_image(mat, sl.VIEW.LEFT)
    frame_shape = list(mat.get_data().shape)  # [H, W, 4] BGRA uint8
    cam.close()

    schema = {
        "note": "Only data physically stored in the SVO2 file is listed here.",
        "file": path,
        "recording": {
            "camera_model":   str(info.camera_model),
            "serial_number":  info.serial_number,
            "firmware_version": sc.firmware_version,
            "total_frames":   cam.get_svo_number_of_frames(),
            "resolution":     {"width": cfg.resolution.width, "height": cfg.resolution.height},
            "fps":            cfg.fps,
        },
        "calibration": {
            "left_camera": {
                "focal_length_px":    {"fx": lc.fx, "fy": lc.fy},
                "principal_point_px": {"cx": lc.cx, "cy": lc.cy},
                "distortion_coeffs":  list(lc.disto),
            },
            "right_camera": {
                "focal_length_px":    {"fx": rc.fx, "fy": rc.fy},
                "principal_point_px": {"cx": rc.cx, "cy": rc.cy},
                "distortion_coeffs":  list(rc.disto),
            },
            "stereo_baseline_m": cal.get_camera_baseline() / 1000.0,
        },
        "per_frame": {
            "left_image":  {"dtype": "uint8", "shape": frame_shape, "format": "BGRA"},
            "right_image": {"dtype": "uint8", "shape": frame_shape, "format": "BGRA"},
            "timestamp":   {"dtype": "int64", "unit": "ms (Unix epoch)"},
        },
        "sensors": {
            "accelerometer": _sensor_entry(sc.accelerometer_parameters),
            "gyroscope":     _sensor_entry(sc.gyroscope_parameters),
            "barometer":     _sensor_entry(sc.barometer_parameters),
            "magnetometer":  _sensor_entry(sc.magnetometer_parameters),
        },
    }

    print(json.dumps(schema, indent=2))


def read_svo2(path: str) -> dict:
    cam = _open(path)
    info = cam.get_camera_information()
    cfg  = info.camera_configuration
    cal  = cfg.calibration_parameters
    lc, rc = cal.left_cam, cal.right_cam
    sc   = info.sensors_configuration

    has_accel = sc.accelerometer_parameters.is_available
    has_gyro  = sc.gyroscope_parameters.is_available
    has_baro  = sc.barometer_parameters.is_available
    has_mag   = sc.magnetometer_parameters.is_available

    result = {
        "file": path,
        "recording": {
            "camera_model":  str(info.camera_model),
            "serial_number": info.serial_number,
            "total_frames":  cam.get_svo_number_of_frames(),
            "resolution":    {"width": cfg.resolution.width, "height": cfg.resolution.height},
            "fps":           cfg.fps,
        },
        "calibration": {
            "left_camera": {
                "focal_length_px":    {"fx": lc.fx, "fy": lc.fy},
                "principal_point_px": {"cx": lc.cx, "cy": lc.cy},
                "distortion_coeffs":  list(lc.disto),
            },
            "right_camera": {
                "focal_length_px":    {"fx": rc.fx, "fy": rc.fy},
                "principal_point_px": {"cx": rc.cx, "cy": rc.cy},
                "distortion_coeffs":  list(rc.disto),
            },
            "stereo_baseline_m": cal.get_camera_baseline() / 1000.0,
        },
        "frames": [],
    }

    runtime = sl.RuntimeParameters()
    sensors = sl.SensorsData()
    frame_idx = 0

    while True:
        status = cam.grab(runtime)
        if status == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
            break
        if status != sl.ERROR_CODE.SUCCESS:
            print(f"Warning: grab failed at frame {frame_idx}: {status}")
            break

        ts = cam.get_timestamp(sl.TIME_REFERENCE.IMAGE).get_milliseconds()
        frame: dict = {"index": frame_idx, "timestamp_ms": ts}

        cam.get_sensors_data(sensors, sl.TIME_REFERENCE.IMAGE)
        imu = sensors.get_imu_data()

        if has_accel:
            a = imu.get_linear_acceleration()
            frame["accelerometer_m_s2"] = {"x": a[0], "y": a[1], "z": a[2]}
        if has_gyro:
            g = imu.get_angular_velocity()
            frame["gyroscope_deg_s"] = {"x": g[0], "y": g[1], "z": g[2]}
        if has_baro:
            b = sensors.get_barometer_data()
            frame["barometer_hpa"] = b.pressure
        if has_mag:
            m = sensors.get_magnetometer_data()
            mf = m.get_magnetic_field_uncalibrated()
            frame["magnetometer_uT"] = {"x": mf[0], "y": mf[1], "z": mf[2]}

        result["frames"].append(frame)
        frame_idx += 1

    cam.close()
    return result


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else SVO_PATH

    if "--schema" in sys.argv:
        schema_svo2(path)
    else:
        data = read_svo2(path)
        with open(OUT_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote {data['total_frames']} frames to {OUT_PATH}")
