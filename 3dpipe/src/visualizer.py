import os
import subprocess
import cv2
import numpy as np
from collections import deque
from pipeline import project_to_pixel, BallKalmanFilter


class FrameVisualizer:
    """Renders tracking and prediction overlays onto video frames."""

    def __init__(
        self, output_path: str, intrinsics: tuple[float, float, float, float],
        fps: int = 30, max_missed: int = 5, prediction_horizon: float = 0.2,
    ):
        self.output_path = output_path
        self.fx, self.fy, self.cx, self.cy = intrinsics
        self.max_missed = max_missed
        self.prediction_horizon = prediction_horizon
        self.trail: deque = deque()
        self.pred_trail: deque = deque()
        self._tmp_path = output_path + ".tmp.mp4"
        self._writer = cv2.VideoWriter(
            self._tmp_path,
            cv2.VideoWriter.fourcc(*"mp4v"),
            fps,
            (1920, 1080),
        )

    def _get_display_position(
        self, smoothed_xyz: tuple[float, float, float] | None,
        kf: BallKalmanFilter, missed: int,
    ) -> tuple[tuple[float, float, float] | None, tuple[float, float, float] | None]:
        """Decide what position to show. Returns (current_xyz, label_xyz)."""
        if not kf.initialized:
            return None, None

        state_xyz = kf.get_position()

        if smoothed_xyz is not None:
            return smoothed_xyz, state_xyz
        if 0 < missed < self.max_missed:
            return state_xyz, state_xyz
        return None, state_xyz

    def draw_frame(
        self,
        frame_rgb: np.ndarray,
        smoothed_xyz: tuple[float, float, float] | None,
        kf: BallKalmanFilter,
        past_pred_xyz: tuple[float, float, float] | None,
        missed: int,
    ) -> None:
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        current_xyz, label_xyz = self._get_display_position(smoothed_xyz, kf, missed)
        detected = missed == 0

        current_pixel = None
        if current_xyz is not None:
            current_pixel = project_to_pixel(
                *current_xyz, self.fx, self.fy, self.cx, self.cy,
            )

        color = (0x3C, 0x63, 0x01) if detected else (0x04, 0x89, 0xFF)
        if current_pixel is not None:
            self.trail.append((current_pixel, color))

        self._draw_trail(frame_bgr)
        self._draw_current(frame_bgr, current_pixel, label_xyz, color)
        self._draw_prediction(frame_bgr, current_pixel, past_pred_xyz)
        self._writer.write(frame_bgr)

    def _draw_trail(self, frame_bgr: np.ndarray) -> None:
        for i in range(1, len(self.trail)):
            cv2.line(frame_bgr, self.trail[i - 1][0], self.trail[i][0], self.trail[i][1], 2)

    def _draw_current(
        self,
        frame_bgr: np.ndarray,
        pixel: tuple[int, int] | None,
        label_xyz: tuple[float, float, float] | None,
        color: tuple[int, int, int],
    ) -> None:
        if pixel is None:
            return
        cv2.circle(frame_bgr, pixel, 12, color, -1)
        if label_xyz is not None:
            lx, ly, lz = label_xyz
            cv2.putText(
                frame_bgr, f"({lx:.2f}, {ly:.2f}, {lz:.2f})",
                (pixel[0] + 20, pixel[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
            )

    _PRED_COLOR = (0x94, 0x01, 0x8A)

    def _draw_prediction(
        self,
        frame_bgr: np.ndarray,
        current_pixel: tuple[int, int] | None,
        past_pred_xyz: tuple[float, float, float] | None,
    ) -> None:
        if past_pred_xyz is not None:
            px, py, pz = past_pred_xyz
            pred_pixel = project_to_pixel(px, py, pz, self.fx, self.fy, self.cx, self.cy)
            if pred_pixel is not None:
                self.pred_trail.append(pred_pixel)
                cv2.circle(frame_bgr, pred_pixel, 12, self._PRED_COLOR, -1)
                if current_pixel is not None:
                    cv2.line(frame_bgr, current_pixel, pred_pixel, (0, 0, 0), 2)
                cv2.putText(
                    frame_bgr, f"({px:.2f}, {py:.2f}, {pz:.2f})",
                    (pred_pixel[0] + 20, pred_pixel[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, self._PRED_COLOR, 2,
                )

        for i in range(1, len(self.pred_trail)):
            cv2.line(frame_bgr, self.pred_trail[i - 1], self.pred_trail[i], self._PRED_COLOR, 2)

    def release(self) -> None:
        self._writer.release()
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", self._tmp_path,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-an", self.output_path,
            ],
            check=True,
        )
        os.remove(self._tmp_path)
