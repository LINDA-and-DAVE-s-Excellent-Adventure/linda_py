from machine import Pin 
from micropython import const
import _thread

from encoding import HammingData
from laser import LindaLaser


# Set up pin values
# Testing on Thing Plus
# RLED_PIN = 21
# GLED_PIN = 19
# DETECTOR_PIN = 16
# LASER_PIN = 25
# SWITCH_PIN = 18

# Testing on WeAct RP2040
RLED_PIN = 18
GLED_PIN = 19
BLED_PIN = 20
SWITCH_PIN = 12
LASER_PIN = 29
DETECTOR_PIN = 7

class Linda():
    def __init__(self):
        print("New LINDA top-level controller")
        # Allocate initial buffers
        self._allocate_buffers()
        self.laser = LindaLaser(memoryview(self.loiter_buffer), memoryview(self.inbox_buffer), memoryview(self.outbox_buffer), 
                                LASER_PIN, DETECTOR_PIN)
        # self.i2c = LindaAmsat()

    def _allocate_buffers(self) -> None:
        # RP2040 has 264KB SRAM. Allocate most of it here for speed
        self.amsat_buffer = bytearray(64000)
        self.inbox_buffer = bytearray(64000)
        self.outbox_buffer = bytearray(64000)
        # Loiter incoming data in top 64 bytes of inbox_buffer
        self.loiter_buffer = self.inbox_buffer[:64]
        # Leave the rest of memory for general usage and garbage collection


    def start(self):
        # Start the laser listener loop in its own thread
        _thread.start_new_thread(self.laser.start, ())
        # Start the Amsat i2c listener 
        # _thread.start_new_thread(self.i2c.start, ())
