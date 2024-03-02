from machine import Pin 
import rp2
import time
import math
import utime
from micropython import const

from lib.encoding import HammingData
# from lib.laser import 

# Set up pins
builtin_led = Pin(25, Pin.OUT)
detector = Pin(16, Pin.IN)
laser = Pin(17, Pin.OUT)
switch = Pin(18, Pin.IN)
gled = Pin(19, Pin.OUT)
yled = Pin(20, Pin.OUT)
rled = Pin(21, Pin.OUT)


if __name__ == "__main__":
    while True:
        # Reset LEDs
        gled.value(0)
        rled.value(0)
        yled.value(0)
        # Check the tx/rx toggle switch
        tx_rx_state = switch.value()
        if tx_rx_state:
            # annoyingly, the sensor sees a laser and outputs 0
            laser_signal = not detector.value()
            if laser_signal == 1:  
                builtin_led.value(1)
                gled.value(1)
                yled.value(1)
                # print("Laser signal detected!")
                laser.value(1)
            else:
                rled.value(1)
                yled.value(1)
                builtin_led.value(0)
                # print("No laser signal.")
                laser.value(0)
        else:
            gled.value(1)
            yled.value(1)
            rled.value(0)
            print("Transmitting!")
            
            time.sleep(2)
