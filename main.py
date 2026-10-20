import cv2
import numpy as np
from scipy.signal import savgol_filter, find_peaks

# --- PHYSICAL CONSTANTS ---
LAMBDA_M = 650e-9       # 650 nm red laser wavelength in meters
DIST_L_M = 0.500        # 50.0 cm (0.500 m) wire-to-screen distance
CALIB_MM = 50.0         # Distance between your 2 ruler clicks (50 mm = 5 cm)

# Calibration globals
calib_points = []
mm_per_pixel = None

def click_calibrate(event, x, y, flags, param):
    global calib_points, mm_per_pixel
    if event == cv2.EVENT_LBUTTONDOWN and len(calib_points) < 2:
        calib_points.append((x, y))
        if len(calib_points) == 2:
            px_dist = np.hypot(calib_points[1][0] - calib_points[0][0],
                               calib_points[1][1] - calib_points[0][1])
            mm_per_pixel = CALIB_MM / px_dist
            print(f"[CALIBRATED] Scale: {mm_per_pixel:.5f} mm/pixel")

# --- CAMERA SETUP ---
CAM_INDEX = 1
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(CAM_INDEX)

cv2.namedWindow("Optical Laser Micrometer")
cv2.setMouseCallback("Optical Laser Micrometer", click_calibrate)

print(f"STEP 1: Click two ruler ticks {int(CALIB_MM)} mm apart on the screen to calibrate.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera frame drop or disconnected. Exiting...")
        break

    display = frame.copy()
    h, w, _ = frame.shape
    center_y = h // 2

    # Define the active detection zone (middle 30% of the screen: 35% to 65%)
    zone_left = int(w * 0.35)
    zone_right = int(w * 0.65)

    # Draw green horizontal scan strip + yellow vertical boundary lines for the active zone
    cv2.rectangle(display, (0, center_y - 10), (w, center_y + 10), (0, 255, 0), 1)
    cv2.line(display, (zone_left, center_y - 25), (zone_left, center_y + 25), (0, 255, 255), 1)
    cv2.line(display, (zone_right, center_y - 25), (zone_right, center_y + 25), (0, 255, 255), 1)

    # Show cyan calibration dots
    for pt in calib_points:
        cv2.circle(display, pt, 4, (255, 255, 0), -1)

    if mm_per_pixel is not None:
        # Extract Red channel and average 20 rows
        red_strip = frame[center_y - 10 : center_y + 10, :, 2]
        profile = np.mean(red_strip, axis=0)

        # Smooth noise
        smooth_profile = savgol_filter(profile, window_length=15, polyorder=3)

        # Invert profile so dark valleys become peaks
        inverted = 255.0 - smooth_profile
        minima, properties = find_peaks(inverted, prominence=8, distance=8)

        # Filter 1: Must be inside the yellow boundary lines (zone_left to zone_right)
        # Filter 2: "True Valley" check — both sides (15 px left and 15 px right) must be brighter than the dip
        valid_indices = []
        for idx, m in enumerate(minima):
            if zone_left < m < zone_right:
                left_shoulder = np.max(smooth_profile[max(0, m - 20):m])
                right_shoulder = np.max(smooth_profile[m + 1:min(w, m + 21)])
                # Both shoulders must rise at least 8 brightness units above the valley floor
                if (left_shoulder - smooth_profile[m] > 8) and (right_shoulder - smooth_profile[m] > 8):
                    valid_indices.append(idx)

        if len(valid_indices) >= 2:
            # Sort by prominence (deepest sharp dips win, not edge cliffs)
            best_two = sorted(valid_indices, key=lambda idx: properties['prominences'][idx], reverse=True)[:2]
            x_left, x_right = sorted([minima[best_two[0]], minima[best_two[1]]])

            delta_px = x_right - x_left
            if delta_px > 0:
                delta_x_mm = delta_px * mm_per_pixel
                delta_x_m = delta_x_mm * 1e-3

                # Fraunhofer Formula: d = (2 * lambda * L) / delta_x
                wire_dia_um = ((2.0 * LAMBDA_M * DIST_L_M) / delta_x_m) * 1e6

                # Draw blue vertical tracking lines on the detected valleys
                cv2.line(display, (x_left, center_y - 30), (x_left, center_y + 30), (255, 0, 0), 2)
                cv2.line(display, (x_right, center_y - 30), (x_right, center_y + 30), (255, 0, 0), 2)

                # Display live results
                cv2.putText(display, f"Wire Dia: {wire_dia_um:.1f} um", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                cv2.putText(display, f"Fringe Gap: {delta_x_mm:.2f} mm ({delta_px} px)", (20, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        # Draw live red intensity graph at bottom of window
        for x in range(1, w):
            y1 = h - 10 - int((smooth_profile[x - 1] / 255.0) * 100)
            y2 = h - 10 - int((smooth_profile[x] / 255.0) * 100)
            cv2.line(display, (x - 1, y1), (x, y2), (0, 0, 255), 2)
    else:
        cv2.putText(display, f"CLICK 2 POINTS {int(CALIB_MM)}mm APART ON RULER", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)

    cv2.imshow("Optical Laser Micrometer", display)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('r'):
        calib_points = []
        mm_per_pixel = None
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()