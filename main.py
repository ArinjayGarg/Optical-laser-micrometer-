"""Automatic wire / hair diameter estimate from a red-laser diffraction pattern.

Hardware: USB UVC webcam, laptop, 650 nm red laser, vertical wire, and a matte
screen. The camera images the screen; it does not look directly at the laser or
at a bare sensor. See README.md for the physical layout and calibration steps.

Install: python -m pip install opencv-python numpy
Run:     python laser_micrometer.py --distance-mm 1500 --wavelength-nm 650
"""

from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

cv2 = None


WINDOW = "Automatic Laser Wire Micrometer"
CSV_PATH = Path("measurements.csv")


def smooth_profile(profile: np.ndarray) -> np.ndarray:
    """Smooth sensor noise without moving fringe positions appreciably."""
    width = max(3, (len(profile) // 250) | 1)
    width = min(width, 7)
    if width % 2 == 0:
        width += 1
    radius = width // 2
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    sigma = max(1.0, width / 5.0)
    kernel = np.exp(-(x * x) / (2.0 * sigma * sigma))
    kernel /= kernel.sum()
    padded = np.pad(profile.astype(np.float64), (radius, radius), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def subpixel_vertex(profile: np.ndarray, index: int) -> float:
    """Estimate a peak/valley location between pixels with a local parabola."""
    if index <= 0 or index >= len(profile) - 1:
        return float(index)
    y0, y1, y2 = map(float, profile[index - 1:index + 2])
    denominator = y0 - 2.0 * y1 + y2
    if abs(denominator) < 1e-9:
        return float(index)
    offset = 0.5 * (y0 - y2) / denominator
    return float(index) + max(-0.5, min(0.5, offset))


def local_minima(profile: np.ndarray, center: int) -> tuple[Optional[float], Optional[float], float]:
    """Return the nearest credible first minima on either side of the main peak."""
    n = len(profile)
    low = float(np.percentile(profile, 10))
    high = float(np.percentile(profile, 95))
    dynamic = high - low
    if dynamic < 12 or n < 40:
        return None, None, 0.0

    prominence_floor = max(5.0, 0.08 * dynamic)
    candidates: list[tuple[int, float]] = []
    radius = max(8, min(60, n // 12))
    for i in range(2, n - 2):
        if not (profile[i] <= profile[i - 1] and profile[i] < profile[i + 1]):
            continue
        left_a = max(0, i - radius)
        right_b = min(n, i + radius + 1)
        left_peak = float(np.max(profile[left_a:i])) if i > left_a else float(profile[i])
        right_peak = float(np.max(profile[i + 1:right_b])) if i + 1 < right_b else float(profile[i])
        prominence = min(left_peak, right_peak) - float(profile[i])
        if prominence >= prominence_floor:
            candidates.append((i, prominence))

    max_distance = n // 3
    left = [item for item in candidates if 3 <= center - item[0] <= max_distance]
    right = [item for item in candidates if 3 <= item[0] - center <= max_distance]
    left_idx = max(left, key=lambda item: item[0])[0] if left else None
    right_idx = min(right, key=lambda item: item[0])[0] if right else None

    confidence = 0.0
    if left_idx is not None and right_idx is not None:
        left_span = center - left_idx
        right_span = right_idx - center
        asymmetry = abs(left_span - right_span) / max(1.0, (left_span + right_span) / 2.0)
        left_prom = next(p for i, p in candidates if i == left_idx)
        right_prom = next(p for i, p in candidates if i == right_idx)
        contrast_score = min(1.0, min(left_prom, right_prom) / max(1.0, 0.3 * dynamic))
        symmetry_score = max(0.0, 1.0 - asymmetry / 0.35)
        confidence = contrast_score * symmetry_score
        if asymmetry > 0.35:
            return None, None, confidence

    left_x = subpixel_vertex(profile, left_idx) if left_idx is not None else None
    right_x = subpixel_vertex(profile, right_idx) if right_idx is not None else None
    return left_x, right_x, confidence


def analyze_frame(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray, Optional[float], Optional[float], Optional[float], float]:
    """Extract a horizontal red-light profile and its center/first minima."""
    height, width = frame.shape[:2]
    y_center = height // 2
    band_half = max(4, int(height * 0.035))
    red_band = frame[max(0, y_center - band_half):min(height, y_center + band_half), :, 2]
    profile = np.median(red_band, axis=0).astype(np.float64)
    smooth = smooth_profile(profile)

    # The central diffraction maximum should be kept in the middle half of the view.
    x0, x1 = int(width * 0.25), int(width * 0.75)
    center_i = x0 + int(np.argmax(smooth[x0:x1]))
    center_x = subpixel_vertex(smooth, center_i)
    left, right, confidence = local_minima(smooth, center_i)
    return red_band, smooth, center_x, left, right, confidence


def draw_profile(frame: np.ndarray, profile: np.ndarray, center: Optional[float], left: Optional[float], right: Optional[float]) -> None:
    """Draw the analyzed red-channel line profile in the lower part of the frame."""
    height, width = frame.shape[:2]
    panel_h = max(90, height // 4)
    top = height - panel_h
    cv2.rectangle(frame, (0, top), (width - 1, height - 1), (18, 28, 36), -1)
    if len(profile) < 2:
        return
    values = np.clip(profile, 0, 255)
    pmin, pmax = float(values.min()), float(values.max())
    if pmax <= pmin:
        return
    points = []
    for x, value in enumerate(values):
        y = top + panel_h - 10 - int((value - pmin) / (pmax - pmin) * (panel_h - 20))
        points.append((x, y))
    cv2.polylines(frame, [np.asarray(points, dtype=np.int32)], False, (80, 220, 220), 1, cv2.LINE_AA)
    for x, color in ((center, (0, 230, 0)), (left, (255, 120, 60)), (right, (255, 120, 60))):
        if x is not None:
            cv2.line(frame, (round(x), top), (round(x), height - 1), color, 1)


def append_measurement(span_px: float, px_per_mm: Optional[float], diameter_um: Optional[float],
                       confidence: float, args: argparse.Namespace, mode: str) -> None:
    exists = CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        if not exists:
            writer.writerow(["timestamp", "mode", "span_px", "px_per_mm", "distance_mm",
                             "wavelength_nm", "diameter_um", "confidence"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"), mode,
                         f"{span_px:.3f}", "" if px_per_mm is None else f"{px_per_mm:.6f}",
                         f"{args.distance_mm:.3f}", f"{args.wavelength_nm:.3f}",
                         "" if diameter_um is None else f"{diameter_um:.3f}", f"{confidence:.3f}"])


def main() -> int:
    global cv2
    try:
        import cv2 as cv2_module
    except ImportError:
        print("OpenCV is missing. Install it with: python -m pip install opencv-python numpy")
        return 4
    cv2 = cv2_module

    parser = argparse.ArgumentParser(description="Measure a wire/hair from its laser-diffraction minima.")
    parser.add_argument("--camera", type=int, default=0, help="USB webcam index (usually 0 or 1).")
    parser.add_argument("--distance-mm", type=float, default=1500.0, help="Wire-to-screen distance in mm.")
    parser.add_argument("--wavelength-nm", type=float, default=650.0, help="Laser wavelength in nm (check its label/specification).")
    parser.add_argument("--reference-diameter-um", type=float, default=None,
                        help="Known reference wire diameter in micrometres; press R while its pattern is visible.")
    parser.add_argument("--calibration-mm", type=float, default=50.0,
                        help="Distance between the two screen-scale marks clicked during C calibration.")
    args = parser.parse_args()
    if args.distance_mm <= 0 or args.wavelength_nm <= 0 or args.calibration_mm <= 0:
        parser.error("distance, wavelength, and calibration length must be positive")

    # Calibration is deliberately session-only. The user must capture a fresh
    # reference or screen scale every run, avoiding a stale value after setup changes.
    px_per_mm = None
    ref_span_px = None

    backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
    cap = cv2.VideoCapture(args.camera, backend)
    if not cap.isOpened():
        print(f"Could not open camera {args.camera}. Close other camera apps or try --camera 1.")
        return 2
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    calibration_clicks: list[tuple[int, int]] = []
    calibrating = False
    last_result: dict = {}

    def on_mouse(event: int, x: int, y: int, _flags: int, _userdata: object) -> None:
        nonlocal px_per_mm, calibrating, calibration_clicks
        if event == cv2.EVENT_LBUTTONDOWN and calibrating:
            calibration_clicks.append((x, y))
            if len(calibration_clicks) == 2:
                (x_a, y_a), (x_b, y_b) = calibration_clicks
                dx, dy = abs(x_b - x_a), abs(y_b - y_a)
                if dx < 10 or dy > max(12, dx * 0.08):
                    calibration_clicks.clear()
                    print("Scale marks must be separated horizontally; please click them again.")
                    return
                px_per_mm = dx / args.calibration_mm
                calibrating = False
                calibration_clicks.clear()
                print(f"Scale calibrated: {px_per_mm:.4f} px/mm using {args.calibration_mm:g} mm.")

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, on_mouse)
    print("Controls: C=scale calibration, R=save known reference wire, S=save result, Q=quit.")
    print("Use the USB webcam only. Lock its focus after calibration; keep it and the screen fixed.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("Camera frame failed. Check the USB connection and camera index.")
                return 3

            _, profile, center, left, right, confidence = analyze_frame(frame)
            last_result = {}  # Never allow S to save a stale frame after the pattern is lost.
            span_px = float(right - left) if left is not None and right is not None else None
            diameter_um = None
            mode = "uncalibrated"
            status = "NO VALID FRINGES - align wire/beam and reduce room light"
            color = (0, 150, 255)

            if span_px is not None and span_px >= 20 and confidence >= 0.15:
                if ref_span_px and args.reference_diameter_um:
                    diameter_um = float(args.reference_diameter_um) * float(ref_span_px) / span_px
                    mode = "reference-ratio"
                    status = f"DIAMETER {diameter_um:.1f} um   (reference-calibrated)"
                    color = (30, 220, 60)
                elif px_per_mm:
                    span_mm = span_px / float(px_per_mm)
                    diameter_um = (2.0 * args.wavelength_nm * args.distance_mm / span_mm) / 1000.0
                    mode = "lambda-L-scale"
                    status = f"DIAMETER {diameter_um:.1f} um   span {span_px:.1f} px / {span_mm:.3f} mm"
                    color = (30, 220, 60)
                else:
                    status = f"FRINGES FOUND: span {span_px:.1f} px - press C to calibrate screen scale"
                    color = (0, 190, 255)

                if diameter_um is not None:
                    last_result = {"span_px": span_px, "diameter_um": diameter_um,
                                   "confidence": confidence, "mode": mode}

            # Mark the minima in the camera image and draw the live one-dimensional profile.
            if left is not None:
                cv2.line(frame, (round(left), 0), (round(left), frame.shape[0] - 1), (255, 150, 40), 1)
            if right is not None:
                cv2.line(frame, (round(right), 0), (round(right), frame.shape[0] - 1), (255, 150, 40), 1)
            if center is not None:
                cv2.line(frame, (round(center), 0), (round(center), frame.shape[0] - 1), (40, 240, 40), 1)
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 54), (18, 28, 36), -1)
            cv2.putText(frame, status, (12, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2, cv2.LINE_AA)
            if args.reference_diameter_um and not ref_span_px:
                hint = f"Reference wire ({args.reference_diameter_um:g} um) visible? Press R to set reference."
            elif not px_per_mm and not ref_span_px:
                hint = f"Press C, then click two marks {args.calibration_mm:g} mm apart on the screen scale."
            else:
                hint = "C recalibrate scale | R set reference | S save measurement | Q quit"
            cv2.putText(frame, hint, (12, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (225, 235, 240), 1, cv2.LINE_AA)
            draw_profile(frame, profile, center, left, right)
            cv2.imshow(WINDOW, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("c"):
                calibrating = True
                calibration_clicks.clear()
                print(f"Click two horizontal scale marks exactly {args.calibration_mm:g} mm apart in the live window.")
            elif key == 27:
                calibrating = False
                calibration_clicks.clear()
            elif key == ord("r"):
                if not args.reference_diameter_um:
                    print("Start with --reference-diameter-um VALUE (known by a micrometer or certified spec).")
                elif span_px is None or confidence < 0.15:
                    print("Reference not saved: no reliable pair of first minima is visible.")
                else:
                    ref_span_px = span_px
                    print(f"Reference captured: {ref_span_px:.2f} px = {args.reference_diameter_um:g} um.")
            elif key == ord("s"):
                if not last_result:
                    print("No valid measurement to save yet.")
                else:
                    append_measurement(last_result["span_px"], px_per_mm,
                                       last_result["diameter_um"], last_result["confidence"],
                                       args, last_result["mode"])
                    print(f"Saved measurement to {CSV_PATH.resolve()}.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
