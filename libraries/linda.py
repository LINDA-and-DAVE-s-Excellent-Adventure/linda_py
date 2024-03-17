from machine import Pin 
from micropython import const
import _thread

from encoding import HammingData
from laser import LindaLaser
# from memory import InboxBuffer, OutboxBuffer


# Set up pin values
# Testing on Thing Plus
RLED_PIN = 19
GLED_PIN = 18
BLED_PIN = 17
DETECTOR_PIN = 20
LASER_PIN = 21
BUTTON_PIN = 22


# # Testing on WeAct RP2040
# RLED_PIN = 18
# GLED_PIN = 19
# BLED_PIN = 20
# SWITCH_PIN = 12
# LASER_PIN = 29
# DETECTOR_PIN = 7

class Linda():
    def __init__(self):
        print("New LINDA top-level controller")
        # Allocate initial buffers
        # inbox = InboxBuffer(64000)
        # outbox = OutboxBuffer(64000)
        # self.laser = LindaLaser(inbox, outbox, LASER_PIN, DETECTOR_PIN)
        # self.i2c = LindaAmsat()

    def start(self):
        # Start the laser listener loop in its own thread
        # _thread.start_new_thread(self.laser.start, ())
        # Start the Amsat i2c listener 
        # _thread.start_new_thread(self.i2c.start, ())
        pass
