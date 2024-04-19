# This consolidates all GPIO pin definitions to a single file
from micropython import const

# Sparkfun Thing Plus
# RLED_PIN = const(19)
# GLED_PIN = const(18)
# BLED_PIN = const(17)
LED_BUILTIN_PIN = const(25)
DETECTOR_PIN = const(20)
LASER_PIN = const(21)
BUTTON_B_PIN = const(17)
BUTTON_R_PIN = const(19)
SWITCH_PIN = const(16)
WS2812_PIN = const(8)
QWIIC_SCL = const(7)
QWIIC_SDA = const(6)

# # Sparkfun Pro Micro RP2040
# RLED_PIN = const(7)
# GLED_PIN = const(6)
# BLED_PIN = const(5)
# BUTTON_PIN = const(3)
# SWITCH_PIN = const(4)
# LASER_PIN = const(9)
# DETECTOR_PIN = const(8)
# WS2812_PIN = const(25)
# QWIIC_SCL = const(17)
# QWIIC_SDA = const(16)
