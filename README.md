# lindapy

Laser Interface Networking Doohickey for AMSAT -- MicroPython Implementation

## Overview

The Laser Interface Networking Doohickey for AMSAT (LINDA) is a subsystem which implements proof-of-concept laser communications for the [AMSAT CubeSatSim](https://github.com/alanbjohnston/CubeSatSim). It is designed around a Sparkfun Thing Plus RP2040 microcontroller, and uses a generic 650nm laser pointer and laser sensor to implement a basic free-space optical communication link between two LINDA subsystems.

### Block Diagram

![Linda Block Diagram](./doc/LINDA%20Block%20Diagram.jpeg)

### Laser Submodule Flowchart

![LINDA Laser Submodule Flowchart](./doc/LINDA%20Laser%20Flowchart.jpeg)

### Installation

This should be able to be run on any RP2040-based microcontroller, although it was developed on a Sparkfun Thing Plus.

#### Micropython

There are plenty of tutorials on how to set up your microcontroller for Micropython, so I won't do that here. Go to the [MicroPython downloads page](https://micropython.org/download/?mcu=rp2040) and get your microcontroller's firmware, flash it, etc etc.

I found that flashing the Sparkfun Thing Plus RP2040 firmware was causing issues, which were remedied by flashing the normal Raspberry Pi Pico version instead.
