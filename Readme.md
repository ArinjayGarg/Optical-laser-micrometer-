
# Automatic Optical Wire Micrometer

## Final project idea

A red laser passes a vertical wire and forms a diffraction pattern on a matte
screen. A USB webcam films the pattern, and a laptop program detects the first
dark minima, calculates the wire diameter, displays the result, and can save
measurements. This is a complete automatic demonstration: the unknown wire's
fringes are read by software, not by eye. The laptop replaces the OV7670/Pico
camera electronics and display.

The college optical bench will be borrowed. The red laser will be purchased,
and the riders and component holders will be made or adapted to fit that bench.
Measure the bench rail before making the riders. Choose a labelled low-power
laser with a stated wavelength and follow the teacher's safety requirements.

## Physical layout

```text
SIDE VIEW (not to scale)

  low-power red laser       vertical taut wire          matte screen
  + beam stop at end               |                  (diffraction bars)
  [LASER] -------------------------|---------------------- ||
                                    |       L = 1.5 m        ||
                                    |                         \
                                    |                          \
                                    |             USB webcam ---- USB ---- laptop
                                    |             about 30 cm from screen
                                    |             aimed at the screen, below beam

  The webcam sees the pattern on the card. It does not look into the laser beam.
```

The wire must be vertical and gently taut. Align the laser horizontally through
the wire's midpoint. Place the matte screen **1.5 m from the wire** and measure
from the wire plane to the screen plane. Put the webcam below the beam axis,
about 30 cm in front of the screen, and aim it at the screen from the laser side.
Keep it outside the beam path. Focus sharply on the card, frame the whole
pattern, and do not move the camera or screen after calibration. A small black
hood around the screen/camera reduces room-light glare.

With a 650 nm laser and a 127 µm wire at L = 1.5 m, the first dark minima are
expected to be about **15.4 mm apart** on the screen. The larger span helps a
budget webcam resolve the pattern. This is an alignment
estimate; the software measures the actual image.

## How the project works

1. The wire blocks part of the beam. Light bends around its edges and
   interferes, making a central bright band with dark minima on either side.
2. The matte card shows the pattern. The USB webcam sends ordinary video frames
   to the laptop.
3. The program averages a narrow horizontal strip through the pattern, finds
   the central bright maximum and the nearest first minimum on each side, and
   calculates their separation.
4. The program converts that separation to a diameter, shows the live image,
   fringe profile, and result, and saves a valid reading to CSV when **S** is
   pressed.

The first-minimum relation for a thin wire is approximately

```text
d = 2 * wavelength * wire-to-screen distance / distance between first minima
```

The software can use either a physical screen scale or a reference wire. The
recommended classroom method is the **reference wire ratio**:

```text
unknown diameter = known reference diameter * reference fringe span / unknown fringe span
```

This ratio uses the same camera, screen, and geometry for both samples. The
known wire's diameter still needs to come from a screw gauge or a trustworthy
specification. The app intentionally requires fresh calibration every time it
starts, so an old camera position cannot silently supply a stale scale.

## Build and run

1. Make/adapt riders to fit the borrowed bench. Secure the purchased laser and
   wire holder to their own riders. Stretch the sample vertically, gently, and
   align the beam through its midpoint.
2. Put the matte screen 1500 mm behind the wire. Add a black beam stop behind
   the screen. Make sure the beam ends there.
3. Mount the webcam about 30 cm in front of the screen, slightly below the beam.
   Aim it at the screen; focus until the fringes are sharp. Reduce room light
   with the hood, and keep the pattern centered in the image.
4. Connect the webcam to the laptop. Install Python 3.10+ and the packages:

   ```text
   python -m pip install opencv-python numpy
   ```
5. Start the program (Windows PowerShell example):

   ```text
   python laser_micrometer.py --camera 0 --distance-mm 1500 --wavelength-nm 650 --reference-diameter-um 127
   ```

   Use the wavelength printed on the laser label/specification. Change camera
   index to `1` if the USB webcam is camera 1. Close video-call apps first.
6. For the most dependable classroom readout, place the known reference wire
   in the holder and wait until the pattern is stable. Press **R** to store its
   fringe span for this session. Replace it with the unknown sample without
   moving the laser, camera, screen, or holder. The software now calculates
   the unknown diameter live.
7. Press **S** to save a valid result to `measurements.csv`; press **Q** to
   close the program. If it says **NO VALID FRINGES**, adjust focus, alignment,
   framing, or room light before recording a result.

To use a ruler/scale fixed in the screen plane instead, press **C** and click
two visible marks exactly 50 mm apart. Keep the scale flat against the screen.
The webcam must see both marks and the complete diffraction pattern.

## What to present

- The physical model showing laser, taut vertical wire, screen, webcam, and
  laptop signal path.
- The live camera image with the central peak and two detected first minima
  marked.
- The displayed diameter and live intensity profile.
- A saved CSV reading and a comparison against the screw-gauge value for the
  reference sample.
- The diffraction formula and explanation that the wire's shadow pattern is
  related to the diffraction from a slit of the same width (Babinet's
  principle).

## Limits and safety

This is a feasible school demonstration, not a guaranteed precision
instrument. Camera focus, image framing, screen texture, room light, wire
alignment, and the reference diameter affect the result. Check the full build
with a known wire before presenting. The code refuses to save when it cannot
find a plausible pair of minima, but it cannot certify the accuracy of the
known reference or the hardware.

Use only a labelled low-power laser approved by the teacher. Keep it fixed,
pointed at the screen/beam stop, and switched off when not measuring. Never
look into the beam or direct it at a person or reflective surface.

## Project files

- `laser_micrometer.py` - webcam-based live measurement program.
- `optical-laser-micrometer-model.svg` - visual layout and signal-flow model.
- `output/pdf/optical-laser-micrometer-blueprint.pdf` - printable build and
  project blueprint.
- `measurements.csv` - created when a valid reading is saved.

## References

- [Current webcam listings below Rs 500 (price-check only; confirm focus, stock, and delivery)](https://www.smartprix.com/computer_webcams/price-below_500)
- [OpenCV camera-frame interface](https://docs.opencv.org/4.13.0/d8/dfe/classcv_1_1VideoCapture.html)
- [Babinet principle and wire diffraction background](https://courses.physics.ucsd.edu/2009/Fall/physics2cl/documents/2CL-F09LectureNotes7.pdf)
- [FDA laser classes and pointer safety](https://www.fda.gov/radiation-emitting-products/laser-products-and-instruments/frequently-asked-questions-about-lasers)
