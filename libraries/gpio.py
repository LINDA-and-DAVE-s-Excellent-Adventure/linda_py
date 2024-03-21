# This consolidates all GPIO pin definitions to a single file
from micropython import const

# Sparkfun Thing Plus
RLED_PIN = const(19)
GLED_PIN = const(18)
BLED_PIN = const(17)
DETECTOR_PIN = const(20)
LASER_PIN = const(21)
BUTTON_PIN = const(22)
SWITCH_PIN = const(16)
WS2812_PIN = const(8)

# # Sparkfun Pro Micro RP2040
# RLED_PIN = const(7)
# GLED_PIN = const(6)
# BLED_PIN = const(5)
# BUTTON_PIN = const(3)
# LASER_PIN = const(9)
# DETECTOR_PIN = const(8)
# WS2812_PIN = const(25)
