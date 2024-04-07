# IOT Project - Cropguard
This project introduces CropGuard, a system that employs a flashlight and a range scanner to deter birds and animals from agricultural fields, thereby eliminating the need for specialized equipment and/or personel for the farmer. The system works on both static and moving animals.

## How it works:
1. Connect Cropguard to your personal computer and set the wanted parameters for a given circular area, choosing parameters such as: Maximal distance, minimal distance, maximal scan angle, minimum scan angle, and area scan speed.
2. Leave the device at the agriculural field, leveled even and towards the guarded area, at the height of 30 cm above ground. (For smaller birds and animals, consider lowering the height)
3. The farmer 'Start Scan' button on his PC which is connected by a USB cable to Cropgurad.
4. The system scans the area and stores a digital copy of distances from the device to the nearest point.
5. The system scans each sweep and detects two points that were different from the scanned background.
6. The system calculates the probable location of the animal in 1 second, turns the device towards it and flashes a directed beam of light at the animal.
7. Goes back to 4.

## Folder description:
ESP32: source code for the esp side (firmware).
PC: source code for the pc side.
Documentation: wiring diagram + basic operating instructions
Unit Tests: tests for individual hardware components.
Parameters: contains description of configurable parameters
Assets: Cropguard logo.

## ESP libraries:
- ESP32Servo by Kevin Herrington, John K. Bennet- version 1.1.2
- ESP32Time by fbiego - version 2.0.6
- HardwareSerial - ESP32 builtin library
- string - ESP32 builtin library, (C++ string).

## Project poster:
</poster>
