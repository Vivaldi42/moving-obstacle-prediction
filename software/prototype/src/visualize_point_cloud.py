"""
Interactive SVO2 point cloud viewer (Open3D only, no Qt/OpenCV GUI).

Controls (focus the Open3D window first):
    Right arrow / N  — next frame
    Left arrow  / P  — previous frame
    Shift + Right    — jump +10 frames
    Shift + Left     — jump -10 frames
    Q                — quit

The window title shows the current frame index and valid point count.
The point cloud is coloured with the left camera RGB image.

Usage:
    python src/visualize_point_cloud.py [frame_index]

Requires:  pip install open3d
Note: needs a display (X11 forwarding when running inside Docker).
"""

import sys
import numpy as np
import open3d as o3d
import pyzed.sl as sl
from pipeline import open_svo, grab_frame


SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_ball_up_a_ramp_and_back_21-45-51.svo2"

# 1 = every pixel (~2 M pts at 1080p), 2 = every 2nd (~500 k), 4 = fast preview
STRIDE = 2

# GLFW key codes used by Open3D
KEY_RIGHT = 262
KEY_LEFT  = 263
KEY_N     = ord("N")
KEY_P     = ord("P")
KEY_Q     = ord("Q")


def build_pcd(xyz_map: np.ndarray, rgb: np.ndarray) -> o3d.geometry.PointCloud:
    h = xyz_map.shape[0]
    xyz_map = xyz_map[h // 2:, ...]
    rgb     = rgb[h // 2:, ...]
    pts    = xyz_map[::STRIDE, ::STRIDE, :3].reshape(-1, 3)
    colors = rgb[::STRIDE, ::STRIDE].reshape(-1, 3).astype(np.float64) / 255.0
    valid  = np.all(np.isfinite(pts), axis=1)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts[valid])
    pcd.colors = o3d.utility.Vector3dVector(colors[valid])
    return pcd


def main() -> None:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    cam = open_svo(SVO_PATH)
    total   = cam.get_svo_number_of_frames()
    mat_rgb = sl.Mat()
    mat_xyz = sl.Mat()

    def load_frame(idx: int):
        cam.set_svo_position(idx)
        return grab_frame(cam, mat_rgb, mat_xyz)

    result = load_frame(start)
    if result is None:
        print("File is empty.")
        cam.close()
        return

    left_rgb, xyz_map = result
    pcd = build_pcd(xyz_map, left_rgb)

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window("SVO2 point cloud", width=1280, height=720)
    vis.add_geometry(pcd)
    vis.add_geometry(o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5))

    # Mutable state shared with key callbacks
    state = {"idx": start, "dirty": False, "quit": False}

    def step(delta: int):
        state["idx"] = max(0, min(total - 1, state["idx"] + delta))
        state["dirty"] = True

    for key, delta in [
        (KEY_RIGHT, +1), (KEY_N, +1),
        (KEY_LEFT,  -1), (KEY_P, -1),
    ]:
        vis.register_key_callback(key, lambda v, d=delta: step(d))

    # Shift + arrow = jump 10 frames (GLFW sends key+400 for shift-modified)
    for key, delta in [(KEY_RIGHT + 400, +10), (KEY_LEFT + 400, -10)]:
        vis.register_key_callback(key, lambda v, d=delta: step(d))

    vis.register_key_callback(KEY_Q, lambda v: state.update({"quit": True}))

    print(f"Opened: {total} frames. Use arrow keys or N/P to navigate. Q to quit.")

    last_loaded = start
    while True:
        if state["quit"] or not vis.poll_events():
            break

        if state["dirty"] and state["idx"] != last_loaded:
            result = load_frame(state["idx"])
            if result is not None:
                left_rgb, xyz_map = result
                new_pcd = build_pcd(xyz_map, left_rgb)
                pcd.points = new_pcd.points
                pcd.colors = new_pcd.colors
                vis.update_geometry(pcd)
                last_loaded = state["idx"]
                n_valid = len(pcd.points)
                n_sub   = (xyz_map.shape[0] // STRIDE) * (xyz_map.shape[1] // STRIDE)
                title   = f"SVO2 point cloud — frame {last_loaded}/{total - 1}  ({n_valid}/{n_sub} pts)"
                vis.get_render_option()  # keeps the window responsive
                print(title)
                vis.get_view_control()  # same
            state["dirty"] = False

        vis.update_renderer()

    cam.close()
    vis.destroy_window()


if __name__ == "__main__":
    main()
