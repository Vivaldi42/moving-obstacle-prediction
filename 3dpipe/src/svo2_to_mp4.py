import os
import sys
import subprocess
import cv2
import pyzed.sl as sl

FPS = 30
RESOLUTION = (1920, 1080)


def convert(svo_path: str, output_path: str) -> None:
    cam = sl.Camera()
    init = sl.InitParameters()
    init.set_from_svo_file(svo_path)
    init.svo_real_time_mode = False

    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        raise RuntimeError(f"Could not open SVO2 file: {status}")

    mat = sl.Mat()
    tmp_path = output_path + ".tmp.mp4"
    writer = cv2.VideoWriter(
        tmp_path, cv2.VideoWriter.fourcc(*"mp4v"), FPS, RESOLUTION,
    )

    frame_count = 0
    while True:
        status = cam.grab()
        if status == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
            break
        if status != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"Grab failed: {status}")

        cam.retrieve_image(mat, sl.VIEW.LEFT)
        frame_bgr = cv2.cvtColor(mat.get_data(), cv2.COLOR_BGRA2BGR)
        writer.write(frame_bgr)
        frame_count += 1

    writer.release()
    cam.close()

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", tmp_path,
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-an", output_path,
        ],
        check=True,
    )
    os.remove(tmp_path)
    print(f"Wrote {frame_count} frames to {output_path}")


if __name__ == "__main__":
    # if len(sys.argv) != 3:
    #     print(f"Usage: {sys.argv[0]} <input.svo2> <output.mp4>")
    #     sys.exit(1)
    # convert(sys.argv[1], sys.argv[2])

    convert("/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-05.svo2", "./output/raw_video.mp4")

