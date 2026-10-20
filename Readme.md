
# Webcam Optical Wire Micrometer

## Project overview

A red laser shines across a thin vertical wire. The wire produces a diffraction
pattern on a matte screen. A USB webcam views the screen from the **front (the
laser-facing side)** and sends video to a computer. A Python/OpenCV program
reads the red brightness profile across the middle of the image, locates two
dark minima, and estimates the wire diameter.

This README describes the code currently supplied as the final program. It
does **not** use a Raspberry Pi Pico, OV7670 camera, OLED, reference-wire
calibration, or CSV saving. The computation runs on the computer connected to
the webcam.

## Physical arrangement

```text
SIDE VIEW — not to scale

 laser                 vertical taut wire                 matte screen
 [red laser] -----------------|-------------------------------||
                               |<------- 500 mm -------------->||
                                                               ||  pattern
                                               webcam -------->||
                                            (in front, on the laser side)
                                                               |
                                                        beam stop behind
                                                        screen, if needed

 Webcam USB -------------------------------> computer running Python
```

1. Secure the laser and wire holder to the optical bench. Stretch the wire
   vertically and gently; align the horizontal beam through its midpoint.
2. Put the matte screen **500 mm from the wire**. Measure from the wire plane
   to the screen plane. This is the distance used by the current code
   (`DIST_L_M = 0.500`).
3. Put the webcam in front of the screen, on the same side as the laser, and
   aim it at the screen. Keep it below or beside the beam so the beam does not
   enter the camera lens. Focus on the screen and frame the complete pattern.
4. Place a ruler flat in the screen plane so two visible marks exactly 50 mm
   apart can be clicked. This is the image-scale calibration required by the
   program. Keep the ruler out of the profile area if possible.
5. Reduce room light and use a beam stop behind the screen. The screen must
   scatter enough light toward the webcam for the pattern to be visible.

## How the program works

- Opens camera index **1** first, then tries the default camera if that fails.
- Uses a 650 nm wavelength and a 500 mm wire-to-screen distance, as set near
  the top of `laser_micrometer.py`.
- Before producing a diameter, requires two mouse clicks on ruler marks that
  are exactly 50 mm apart. The clicks set the screen scale in mm per image
  pixel. Click again after pressing **R** to recalibrate.
- Averages the webcam's red channel over 20 image rows at the vertical centre.
- Smooths that profile and searches the middle 30% of the image for dark
  valleys. It chooses the two strongest accepted valleys and treats their
  spacing as the distance between the first minima.
- Calculates the estimated diameter using

  ```text
  d = 2 × wavelength × wire-to-screen distance / first-minima separation
  ```
- Shows the live camera image, profile, detected minima, fringe separation,
  and estimated diameter.

The 50 mm ruler calibration converts image pixels to screen distance. It does
not correct perspective or lens distortion, so keep the webcam facing the
screen as square-on as practical and do not move it after calibration.

## Install and run

Install Python 3 and the required packages:

```text
python -m pip install opencv-python numpy scipy
```

From the project folder, run:

```text
python laser_micrometer.py
```

The camera index is currently set in the script as `CAM_INDEX = 1`. If the
program opens the wrong camera, change it to `0` (or the index used by your
computer) and run again. Close video-call and camera apps if they are using
the webcam.

### Controls

- **Left-click twice:** calibrate using two ruler marks 50 mm apart.
- **R:** clear calibration; click the two marks again.
- **Q:** quit.

The current code does not save results to a file and does not have an **S**
measurement-save control.

## Important code notes before relying on readings

The program is suitable as a project demonstration, but its current valley
selection is a simple heuristic. It picks the two strongest valleys in the
search region; it does not confirm that one is on each side of the central
maximum, nor that they are the nearest first minima. A reflection, screen
texture, shadow, or camera artifact could therefore be mistaken for a fringe.
Only accept a result when the live profile visibly shows a central bright
maximum and a clear dark minimum on each side, with the blue markers on those
two minima.

Suggested code improvements before final submission:

1. Find the central bright maximum first, then select the nearest valid dark
   minimum to its left and right. Reject a pair unless it is approximately
   symmetric around the centre.
2. Check that `px_dist` is nonzero before calculating `mm_per_pixel`, and
   reject clicks too close together. Keep clicks on the same horizontal ruler
   line to avoid scale error from diagonal separation.
3. Check that the frame is large enough for the Savitzky–Golay window and
   clamp the 20-row scan band at the image boundaries.
4. Add optional controls for camera index, laser wavelength, and measured
   wire-to-screen distance instead of editing constants in the source.
5. Add a save function only if the project needs a results log; the pasted
   final code currently has none.

For a 650 nm laser, 500 mm distance, and a 127 µm wire, the expected spacing
between the first minima is about **5.1 mm**. This is a planning estimate;
actual camera focus, screen scattering, alignment, scale calibration, and
fringe selection affect the result. Verify the behavior with a known wire
before presenting and compare against a screw-gauge measurement.

## Safety

Use a labelled, low-power laser approved by your teacher. Secure it so the
beam terminates at the screen/beam stop. Switch it off when adjusting the
wire, webcam, or screen. Never look into the beam or aim it at a person or
reflective surface.

## Project files

- `laser_micrometer.py` — current webcam-based live analysis program.
- `optical-laser-micrometer-model.svg` — project layout illustration; update
  it if its geometry or signal-flow labels disagree with this README.
- `output/pdf/optical-laser-micrometer-blueprint.pdf` — printable blueprint;
  check that its distances and calibration description match this 500 mm,
  ruler-calibrated version before submitting it.

# Webcam Optical Wire Micrometer

## Project overview

A red laser shines across a thin vertical wire. The wire produces a diffraction
pattern on a matte screen. A USB webcam views the screen from the **front (the
laser-facing side)** and sends video to a computer. A Python/OpenCV program
reads the red brightness profile across the middle of the image, locates two
dark minima, and estimates the wire diameter.

This README describes the code currently supplied as the final program. It
does **not** use a Raspberry Pi Pico, OV7670 camera, OLED, reference-wire
calibration, or CSV saving. The computation runs on the computer connected to
the webcam.

## Physical arrangement

```text
SIDE VIEW — not to scale

 laser                 vertical taut wire                 matte screen
 [red laser] -----------------|-------------------------------||
                               |<------- 500 mm -------------->||
                                                               ||  pattern
                                               webcam -------->||
                                            (in front, on the laser side)
                                                               |
                                                        beam stop behind
                                                        screen, if needed

 Webcam USB -------------------------------> computer running Python
```

1. Secure the laser and wire holder to the optical bench. Stretch the wire
   vertically and gently; align the horizontal beam through its midpoint.
2. Put the matte screen **500 mm from the wire**. Measure from the wire plane
   to the screen plane. This is the distance used by the current code
   (`DIST_L_M = 0.500`).
3. Put the webcam in front of the screen, on the same side as the laser, and
   aim it at the screen. Keep it below or beside the beam so the beam does not
   enter the camera lens. Focus on the screen and frame the complete pattern.
4. Place a ruler flat in the screen plane so two visible marks exactly 50 mm
   apart can be clicked. This is the image-scale calibration required by the
   program. Keep the ruler out of the profile area if possible.
5. Reduce room light and use a beam stop behind the screen. The screen must
   scatter enough light toward the webcam for the pattern to be visible.

## How the program works

- Opens camera index **1** first, then tries the default camera if that fails.
- Uses a 650 nm wavelength and a 500 mm wire-to-screen distance, as set near
  the top of `laser_micrometer.py`.
- Before producing a diameter, requires two mouse clicks on ruler marks that
  are exactly 50 mm apart. The clicks set the screen scale in mm per image
  pixel. Click again after pressing **R** to recalibrate.
- Averages the webcam's red channel over 20 image rows at the vertical centre.
- Smooths that profile and searches the middle 30% of the image for dark
  valleys. It chooses the two strongest accepted valleys and treats their
  spacing as the distance between the first minima.
- Calculates the estimated diameter using

  ```text
  d = 2 × wavelength × wire-to-screen distance / first-minima separation
  ```
- Shows the live camera image, profile, detected minima, fringe separation,
  and estimated diameter.

The 50 mm ruler calibration converts image pixels to screen distance. It does
not correct perspective or lens distortion, so keep the webcam facing the
screen as square-on as practical and do not move it after calibration.

## Install and run

Install Python 3 and the required packages:

```text
python -m pip install opencv-python numpy scipy
```

From the project folder, run:

```text
python laser_micrometer.py
```

The camera index is currently set in the script as `CAM_INDEX = 1`. If the
program opens the wrong camera, change it to `0` (or the index used by your
computer) and run again. Close video-call and camera apps if they are using
the webcam.

### Controls

- **Left-click twice:** calibrate using two ruler marks 50 mm apart.
- **R:** clear calibration; click the two marks again.
- **Q:** quit.

The current code does not save results to a file and does not have an **S**
measurement-save control.

## Important code notes before relying on readings

The program is suitable as a project demonstration, but its current valley
selection is a simple heuristic. It picks the two strongest valleys in the
search region; it does not confirm that one is on each side of the central
maximum, nor that they are the nearest first minima. A reflection, screen
texture, shadow, or camera artifact could therefore be mistaken for a fringe.
Only accept a result when the live profile visibly shows a central bright
maximum and a clear dark minimum on each side, with the blue markers on those
two minima.

Suggested code improvements before final submission:

1. Find the central bright maximum first, then select the nearest valid dark
   minimum to its left and right. Reject a pair unless it is approximately
   symmetric around the centre.
2. Check that `px_dist` is nonzero before calculating `mm_per_pixel`, and
   reject clicks too close together. Keep clicks on the same horizontal ruler
   line to avoid scale error from diagonal separation.
3. Check that the frame is large enough for the Savitzky–Golay window and
   clamp the 20-row scan band at the image boundaries.
4. Add optional controls for camera index, laser wavelength, and measured
   wire-to-screen distance instead of editing constants in the source.
5. Add a save function only if the project needs a results log; the pasted
   final code currently has none.

For a 650 nm laser, 500 mm distance, and a 127 µm wire, the expected spacing
between the first minima is about **5.1 mm**. This is a planning estimate;
actual camera focus, screen scattering, alignment, scale calibration, and
fringe selection affect the result. Verify the behavior with a known wire
before presenting and compare against a screw-gauge measurement.

## Safety

Use a labelled, low-power laser approved by your teacher. Secure it so the
beam terminates at the screen/beam stop. Switch it off when adjusting the
wire, webcam, or screen. Never look into the beam or aim it at a person or
reflective surface.

## Project files

- `laser_micrometer.py` — current webcam-based live analysis program.
- `optical-laser-micrometer-model.svg` — project layout illustration; update
  it if its geometry or signal-flow labels disagree with this README.
- `output/pdf/optical-laser-micrometer-blueprint.pdf` — printable blueprint;
  check that its distances and calibration description match this 500 mm,
  ruler-calibrated version before submitting it.
