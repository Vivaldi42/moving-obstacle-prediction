from __future__ import annotations

import argparse
import csv
import math
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import pandas as pd
import pyzed.sl as sl
from ultralytics import YOLO


YOLO_CONFIDENCE_THRESHOLD = 0.5
TRACKING_MAX_DISTANCE_PIXELS = 100.0
TRACKING_MAX_DISTANCE_MM = 200.0
MIN_HISTORY_FRAMES = 3
PREDICTION_HORIZON_SEC = 0.5
FPS = 30.0
CAMERA_FX = 534.0900
CAMERA_FY = 534.9450
CAMERA_CX = 632.0850
CAMERA_CY = 353.6965
DEPTH_MIN_MM = 100.0
DEPTH_MAX_MM = 5000.0
COCO_SPORTS_BALL_CLASS = 32
DEBUG_FRAME_LIMIT = 10
TRACK_HISTORY_LENGTH = 10
MAX_PREDICTION_MISSES = 5
DEFAULT_MODEL_PATH = "yolov8n.pt"
DEPTH_PATCH_RADIUS_PX = 4


@dataclass
class Detection3D:
    bbox: tuple[int, int, int, int]
    confidence: float
    pixel_center: tuple[int, int]
    world_pos_mm: tuple[float, float, float]


@dataclass
class Track:
    track_id: int
    current_pos: tuple[float, float, float]
    current_pixel: tuple[int, int]
    position_history: deque[tuple[float, float, float]] = field(
        default_factory=lambda: deque(maxlen=TRACK_HISTORY_LENGTH)
    )
    pixel_history: deque[tuple[int, int]] = field(
        default_factory=lambda: deque(maxlen=TRACK_HISTORY_LENGTH)
    )
    velocity: tuple[float, float, float] = (0.0, 0.0, 0.0)
    missed_frames: int = 0

    def append(self, position_mm: tuple[float, float, float], pixel_center: tuple[int, int]) -> None:
        self.current_pos = position_mm
        self.current_pixel = pixel_center
        self.position_history.append(position_mm)
        self.pixel_history.append(pixel_center)


class FrameExtractor:
    """Extract RGB and depth from SVO2."""

    def __init__(self, svo_path: str | Path) -> None:
        self.svo_path = str(svo_path)
        self.camera = sl.Camera()
        self.init_params = sl.InitParameters()
        self.init_params.set_from_svo_file(self.svo_path)
        self.init_params.svo_real_time_mode = False
        self.init_params.depth_mode = sl.DEPTH_MODE.ULTRA
        self.init_params.coordinate_units = sl.UNIT.MILLIMETER
        self.init_params.camera_disable_self_calib = True

        status = self.camera.open(self.init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"Failed to open SVO2 file '{self.svo_path}': {status}")

        self.runtime_params = sl.RuntimeParameters()
        self.left_image = sl.Mat()
        self.depth_measure = sl.Mat()
        self.total_frames = int(self.camera.get_svo_number_of_frames())

    def get_total_frames(self) -> int:
        return self.total_frames

    def get_resolution(self) -> tuple[int, int]:
        info = self.camera.get_camera_information()
        resolution = info.camera_configuration.resolution
        return int(resolution.width), int(resolution.height)

    def get_frame(self, frame_idx: int) -> tuple[np.ndarray | None, np.ndarray | None, bool]:
        status = self.camera.set_svo_position(frame_idx)
        if status != sl.ERROR_CODE.SUCCESS:
            return None, None, False

        grab_status = self.camera.grab(self.runtime_params)
        if grab_status != sl.ERROR_CODE.SUCCESS:
            return None, None, False

        self.camera.retrieve_image(self.left_image, sl.VIEW.LEFT)
        self.camera.retrieve_measure(self.depth_measure, sl.MEASURE.DEPTH)

        bgra = self.left_image.get_data()
        depth_map = self.depth_measure.get_data()
        if bgra is None or depth_map is None:
            return None, None, False

        rgb_frame = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGB)
        depth_map = np.nan_to_num(depth_map, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        return rgb_frame, depth_map, True

    def close(self) -> None:
        self.camera.close()


class BallDetector:
    """YOLO detection."""

    def __init__(self, confidence_threshold: float = YOLO_CONFIDENCE_THRESHOLD, model_path: str = DEFAULT_MODEL_PATH) -> None:
        self.confidence_threshold = confidence_threshold
        self.model = YOLO(model_path)

    def detect(self, rgb_frame: np.ndarray) -> list[tuple[int, int, int, int, float]]:
        results = self.model(rgb_frame, verbose=False)
        detections: list[tuple[int, int, int, int, float]] = []

        if not results:
            return detections

        boxes = results[0].boxes
        if boxes is None:
            return detections

        for box in boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            if class_id != COCO_SPORTS_BALL_CLASS or confidence < self.confidence_threshold:
                continue

            x_min, y_min, x_max, y_max = box.xyxy[0].detach().cpu().numpy().astype(int)
            detections.append((x_min, y_min, x_max, y_max, confidence))

        return detections


class Projector3D:
    """Convert pixel to 3D world coordinates."""

    def __init__(
        self,
        fx: float,
        fy: float,
        cx: float,
        cy: float,
        depth_patch_radius_px: int = DEPTH_PATCH_RADIUS_PX,
    ) -> None:
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.depth_patch_radius_px = depth_patch_radius_px

    def project(
        self,
        bbox: tuple[int, int, int, int],
        depth_map: np.ndarray,
    ) -> tuple[tuple[float, float, float], tuple[int, int]] | None:
        x_min, y_min, x_max, y_max = bbox
        center_x = int(round((x_min + x_max) / 2.0))
        center_y = int(round((y_min + y_max) / 2.0))

        if center_y < 0 or center_y >= depth_map.shape[0] or center_x < 0 or center_x >= depth_map.shape[1]:
            return None

        z_mm = self._resolve_depth_mm(depth_map, center_x, center_y, bbox)
        if z_mm is None:
            return None

        x_mm = (center_x - self.cx) * z_mm / self.fx
        y_mm = (center_y - self.cy) * z_mm / self.fy
        return (x_mm, y_mm, z_mm), (center_x, center_y)

    def _resolve_depth_mm(
        self,
        depth_map: np.ndarray,
        center_x: int,
        center_y: int,
        bbox: tuple[int, int, int, int],
    ) -> float | None:
        center_depth = float(depth_map[center_y, center_x])
        if self._is_valid_depth(center_depth):
            return center_depth

        x_min, y_min, x_max, y_max = bbox
        patch_radius = self.depth_patch_radius_px
        patch_x_min = max(0, center_x - patch_radius)
        patch_x_max = min(depth_map.shape[1], center_x + patch_radius + 1)
        patch_y_min = max(0, center_y - patch_radius)
        patch_y_max = min(depth_map.shape[0], center_y + patch_radius + 1)
        patch = depth_map[patch_y_min:patch_y_max, patch_x_min:patch_x_max]
        valid_patch_values = patch[
            np.isfinite(patch)
            & (patch >= DEPTH_MIN_MM)
            & (patch <= DEPTH_MAX_MM)
        ]
        if valid_patch_values.size > 0:
            return float(np.median(valid_patch_values))

        bbox_x_min = max(0, min(x_min, x_max))
        bbox_x_max = min(depth_map.shape[1], max(x_min, x_max) + 1)
        bbox_y_min = max(0, min(y_min, y_max))
        bbox_y_max = min(depth_map.shape[0], max(y_min, y_max) + 1)
        bbox_patch = depth_map[bbox_y_min:bbox_y_max, bbox_x_min:bbox_x_max]
        valid_bbox_values = bbox_patch[
            np.isfinite(bbox_patch)
            & (bbox_patch >= DEPTH_MIN_MM)
            & (bbox_patch <= DEPTH_MAX_MM)
        ]
        if valid_bbox_values.size == 0:
            return None

        return float(np.percentile(valid_bbox_values, 35))

    @staticmethod
    def _is_valid_depth(value: float) -> bool:
        return math.isfinite(value) and DEPTH_MIN_MM <= value <= DEPTH_MAX_MM


class CentroidTracker:
    """Nearest neighbor tracking."""

    def __init__(
        self,
        max_distance_pixels: float = TRACKING_MAX_DISTANCE_PIXELS,
        max_distance_mm: float = TRACKING_MAX_DISTANCE_MM,
        fps: float = FPS,
        max_prediction_misses: int = MAX_PREDICTION_MISSES,
    ) -> None:
        self.max_distance_pixels = max_distance_pixels
        self.max_distance_mm = max_distance_mm
        self.dt = 1.0 / fps
        self.max_prediction_misses = max_prediction_misses
        self.next_track_id = 1
        self.tracks: dict[int, Track] = {}

    def update(self, detections_3d: list[Detection3D]) -> list[Track]:
        if not detections_3d:
            return self._advance_without_detections()

        unmatched_track_ids = set(self.tracks.keys())
        unmatched_detections = set(range(len(detections_3d)))
        candidate_pairs: list[tuple[float, int, int]] = []

        for track_id, track in self.tracks.items():
            for det_index, detection in enumerate(detections_3d):
                pixel_distance = self._pixel_distance(track.current_pixel, detection.pixel_center)
                mm_distance = self._mm_distance(track.current_pos, detection.world_pos_mm)
                if pixel_distance <= self.max_distance_pixels and mm_distance <= self.max_distance_mm:
                    candidate_pairs.append((mm_distance, track_id, det_index))

        candidate_pairs.sort(key=lambda item: item[0])
        for _, track_id, det_index in candidate_pairs:
            if track_id not in unmatched_track_ids or det_index not in unmatched_detections:
                continue
            self._update_track(self.tracks[track_id], detections_3d[det_index])
            unmatched_track_ids.remove(track_id)
            unmatched_detections.remove(det_index)

        for track_id in unmatched_track_ids:
            track = self.tracks[track_id]
            track.missed_frames += 1
            if len(track.position_history) >= 2:
                predicted_pos = tuple(
                    current + velocity * self.dt
                    for current, velocity in zip(track.current_pos, track.velocity)
                )
                track.append(predicted_pos, track.current_pixel)

        for det_index in unmatched_detections:
            self._create_track(detections_3d[det_index])

        expired_ids = [
            track_id
            for track_id, track in self.tracks.items()
            if track.missed_frames > self.max_prediction_misses
        ]
        for track_id in expired_ids:
            del self.tracks[track_id]

        return list(self.tracks.values())

    def _advance_without_detections(self) -> list[Track]:
        expired_ids: list[int] = []
        for track_id, track in self.tracks.items():
            track.missed_frames += 1
            if len(track.position_history) >= 2:
                predicted_pos = tuple(
                    current + velocity * self.dt
                    for current, velocity in zip(track.current_pos, track.velocity)
                )
                track.append(predicted_pos, track.current_pixel)
            if track.missed_frames > self.max_prediction_misses:
                expired_ids.append(track_id)

        for track_id in expired_ids:
            del self.tracks[track_id]

        return list(self.tracks.values())

    def _create_track(self, detection: Detection3D) -> None:
        track = Track(
            track_id=self.next_track_id,
            current_pos=detection.world_pos_mm,
            current_pixel=detection.pixel_center,
        )
        track.append(detection.world_pos_mm, detection.pixel_center)
        self.tracks[self.next_track_id] = track
        self.next_track_id += 1

    def _update_track(self, track: Track, detection: Detection3D) -> None:
        previous_pos = track.current_pos
        track.append(detection.world_pos_mm, detection.pixel_center)
        track.missed_frames = 0
        track.velocity = tuple(
            (current - previous) / self.dt
            for current, previous in zip(track.current_pos, previous_pos)
        )

    @staticmethod
    def _pixel_distance(point_a: tuple[int, int], point_b: tuple[int, int]) -> float:
        return float(np.linalg.norm(np.array(point_a, dtype=np.float32) - np.array(point_b, dtype=np.float32)))

    @staticmethod
    def _mm_distance(point_a: tuple[float, float, float], point_b: tuple[float, float, float]) -> float:
        return float(np.linalg.norm(np.array(point_a, dtype=np.float32) - np.array(point_b, dtype=np.float32)))


class PhysicsPredictor:
    """Constant velocity prediction."""

    def __init__(
        self,
        min_history_frames: int = MIN_HISTORY_FRAMES,
        prediction_horizon_sec: float = PREDICTION_HORIZON_SEC,
        fps: float = FPS,
    ) -> None:
        self.min_history_frames = min_history_frames
        self.prediction_horizon_sec = prediction_horizon_sec
        self.dt = 1.0 / fps

    def predict(
        self,
        position_history: Iterable[tuple[float, float, float]],
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
        history = list(position_history)
        if len(history) < self.min_history_frames:
            return None

        pos_previous = np.array(history[-2], dtype=np.float32)
        pos_current = np.array(history[-1], dtype=np.float32)
        velocity = tuple(((pos_current - pos_previous) / self.dt).tolist())
        prediction = tuple((pos_current + np.array(velocity, dtype=np.float32) * self.prediction_horizon_sec).tolist())
        return prediction, velocity


class Visualizer:
    """Draw overlays and save video."""

    def __init__(self, output_path: str | Path, fps: float = FPS, resolution: tuple[int, int] = (1280, 720)) -> None:
        self.output_path = str(output_path)
        self.resolution = resolution
        self.writer = self._open_writer(self.output_path, fps, resolution)

    def draw_frame(
        self,
        rgb_frame: np.ndarray,
        detections: list[Detection3D],
        tracks: list[Track],
        predictions: dict[int, tuple[float, float, float]],
    ) -> np.ndarray:
        frame_bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        for detection in detections:
            x_min, y_min, x_max, y_max = detection.bbox
            cv2.rectangle(frame_bgr, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
            cv2.circle(frame_bgr, detection.pixel_center, 5, (0, 0, 255), -1)

        for track in tracks:
            pixel_points = list(track.pixel_history)
            if len(pixel_points) >= 2:
                for start, end in zip(pixel_points[:-1], pixel_points[1:]):
                    cv2.line(frame_bgr, start, end, (0, 255, 0), 2)

            predicted_world = predictions.get(track.track_id)
            if predicted_world is not None and len(track.pixel_history) >= 2:
                last_point = track.pixel_history[-1]
                prev_point = track.pixel_history[-2]
                delta = (last_point[0] - prev_point[0], last_point[1] - prev_point[1])
                predicted_pixel = (
                    int(round(last_point[0] + delta[0] * PREDICTION_HORIZON_SEC * FPS)),
                    int(round(last_point[1] + delta[1] * PREDICTION_HORIZON_SEC * FPS)),
                )
                self._draw_dashed_line(frame_bgr, last_point, predicted_pixel, (0, 255, 255), 2)

            x_mm, y_mm, z_mm = track.current_pos
            label = f"id:{track.track_id} X:{x_mm:.0f} Y:{y_mm:.0f} Z:{z_mm:.0f} mm"
            text_origin = (track.current_pixel[0] + 8, max(25, track.current_pixel[1] - 12))
            cv2.putText(
                frame_bgr,
                label,
                text_origin,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        return frame_bgr

    def write_frame(self, frame: np.ndarray) -> None:
        if frame.shape[1] != self.resolution[0] or frame.shape[0] != self.resolution[1]:
            frame = cv2.resize(frame, self.resolution)
        self.writer.write(frame)

    def finalize(self) -> None:
        self.writer.release()

    @staticmethod
    def _open_writer(output_path: str, fps: float, resolution: tuple[int, int]) -> cv2.VideoWriter:
        for codec in ("mp4v", "avc1", "H264"):
            writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*codec), fps, resolution)
            if writer.isOpened():
                return writer
        raise RuntimeError(f"Failed to open video writer for '{output_path}'")

    @staticmethod
    def _draw_dashed_line(
        frame: np.ndarray,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        thickness: int,
        dash_length: int = 8,
    ) -> None:
        distance = int(math.dist(start, end))
        if distance == 0:
            return

        for offset in range(0, distance, dash_length * 2):
            segment_start_ratio = offset / distance
            segment_end_ratio = min(offset + dash_length, distance) / distance
            x1 = int(round(start[0] + (end[0] - start[0]) * segment_start_ratio))
            y1 = int(round(start[1] + (end[1] - start[1]) * segment_start_ratio))
            x2 = int(round(start[0] + (end[0] - start[0]) * segment_end_ratio))
            y2 = int(round(start[1] + (end[1] - start[1]) * segment_end_ratio))
            cv2.line(frame, (x1, y1), (x2, y2), color, thickness)


def save_csv(rows: list[dict[str, float | int]], output_csv: str | Path) -> None:
    columns = [
        "frame_id",
        "track_id",
        "x",
        "y",
        "z",
        "vx",
        "vy",
        "vz",
        "pred_x_0.5s",
        "pred_y_0.5s",
        "pred_z_0.5s",
    ]
    dataframe = pd.DataFrame(rows, columns=columns)
    dataframe = dataframe.fillna(0.0)
    dataframe.to_csv(output_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    if dataframe.isna().any().any():
        raise ValueError("CSV output contains NaN values after fill operation.")


def save_debug_frame(frame: np.ndarray, debug_dir: Path, frame_id: int) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    debug_path = debug_dir / f"frame_{frame_id:05d}.jpg"
    cv2.imwrite(str(debug_path), frame)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect, track, and predict a rolling tennis ball from a ZED 2i SVO2 file."
    )
    parser.add_argument("svo_path", help="Path to the input .svo2 file")
    parser.add_argument("--output-csv", default="output_detections.csv", help="CSV output path")
    parser.add_argument("--output-video", default="output_video.mp4", help="Annotated video output path")
    parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH, help="YOLO model path")
    parser.add_argument("--confidence", type=float, default=YOLO_CONFIDENCE_THRESHOLD, help="YOLO confidence threshold")
    parser.add_argument("--debug-dir", default="debug_frames", help="Directory for saved debug frames")
    return parser.parse_args()


def main(svo_path: str, output_csv: str, output_video: str, model_path: str = DEFAULT_MODEL_PATH, confidence: float = YOLO_CONFIDENCE_THRESHOLD, debug_dir: str = "debug_frames") -> int:
    """Main pipeline orchestration."""
    frame_extractor = FrameExtractor(svo_path)
    detector = BallDetector(confidence_threshold=confidence, model_path=model_path)
    projector = Projector3D(CAMERA_FX, CAMERA_FY, CAMERA_CX, CAMERA_CY)
    tracker = CentroidTracker(
        max_distance_pixels=TRACKING_MAX_DISTANCE_PIXELS,
        max_distance_mm=TRACKING_MAX_DISTANCE_MM,
        fps=FPS,
    )
    predictor = PhysicsPredictor(
        min_history_frames=MIN_HISTORY_FRAMES,
        prediction_horizon_sec=PREDICTION_HORIZON_SEC,
        fps=FPS,
    )
    visualizer = Visualizer(output_video, fps=FPS, resolution=frame_extractor.get_resolution())

    output_rows: list[dict[str, float | int]] = []
    debug_path = Path(debug_dir)
    total_frames = frame_extractor.get_total_frames()

    try:
        for frame_id in range(total_frames):
            start_time = time.perf_counter()
            rgb_frame, depth_map, is_valid = frame_extractor.get_frame(frame_id)
            if not is_valid or rgb_frame is None or depth_map is None:
                print(f"frame_id={frame_id} num_detections=0 num_tracks=0 inference_time_ms=0.00")
                continue

            raw_detections = detector.detect(rgb_frame)
            detections_3d: list[Detection3D] = []
            for x_min, y_min, x_max, y_max, det_confidence in raw_detections:
                projection = projector.project((x_min, y_min, x_max, y_max), depth_map)
                if projection is None:
                    continue
                world_pos_mm, pixel_center = projection
                detections_3d.append(
                    Detection3D(
                        bbox=(x_min, y_min, x_max, y_max),
                        confidence=det_confidence,
                        pixel_center=pixel_center,
                        world_pos_mm=world_pos_mm,
                    )
                )

            tracks = tracker.update(detections_3d)
            predictions: dict[int, tuple[float, float, float]] = {}
            for track in tracks:
                prediction_result = predictor.predict(track.position_history)
                predicted_pos = (0.0, 0.0, 0.0)
                if prediction_result is None:
                    velocity = track.velocity
                else:
                    predicted_pos, velocity = prediction_result
                    track.velocity = velocity
                    predictions[track.track_id] = predicted_pos

                output_rows.append(
                    {
                        "frame_id": frame_id,
                        "track_id": track.track_id,
                        "x": float(track.current_pos[0]),
                        "y": float(track.current_pos[1]),
                        "z": float(track.current_pos[2]),
                        "vx": float(track.velocity[0]),
                        "vy": float(track.velocity[1]),
                        "vz": float(track.velocity[2]),
                        "pred_x_0.5s": float(predicted_pos[0]),
                        "pred_y_0.5s": float(predicted_pos[1]),
                        "pred_z_0.5s": float(predicted_pos[2]),
                    }
                )

            annotated_frame = visualizer.draw_frame(rgb_frame, detections_3d, tracks, predictions)
            visualizer.write_frame(annotated_frame)

            if frame_id < DEBUG_FRAME_LIMIT:
                save_debug_frame(annotated_frame, debug_path, frame_id)

            inference_time_ms = (time.perf_counter() - start_time) * 1000.0
            print(
                f"frame_id={frame_id} "
                f"num_detections={len(detections_3d)} "
                f"num_tracks={len(tracks)} "
                f"inference_time_ms={inference_time_ms:.2f}"
            )
    finally:
        frame_extractor.close()
        visualizer.finalize()

    save_csv(output_rows, output_csv)
    return 0


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(
        main(
            svo_path=arguments.svo_path,
            output_csv=arguments.output_csv,
            output_video=arguments.output_video,
            model_path=arguments.model_path,
            confidence=arguments.confidence,
            debug_dir=arguments.debug_dir,
        )
    )
