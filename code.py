import machine
from machine import Pin 
import time
import neopixel
import math

builtin_led = Pin(25, Pin.OUT)
detector = Pin(16, Pin.IN)
laser = Pin(17, Pin.OUT)
switch = Pin(18, Pin.IN)
gled = Pin(19, Pin.OUT)
yled = Pin(20, Pin.OUT)
rled = Pin(21, Pin.OUT)

np_pin = machine.Pin(8, Pin.OUT, Pin.PULL_DOWN)
np = neopixel.NeoPixel(np_pin, n=1)
num_steps = 360
step = 0
brightness = 1

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

def set_color_wheel(step):
    # Calculate RGB values based on color wheel position with smooth transitions
    r = int(127.5 * (math.sin(step * math.pi / (num_steps/2)) + 1))
    g = int(127.5 * (math.sin((step + num_steps/3) * math.pi / (num_steps/2)) + 1))
    b = int(127.5 * (math.sin((step + 2*num_steps/3) * math.pi / (num_steps/2)) + 1)) 

    np[0] = (int(r * brightness), int(g * brightness), int(b * brightness))  
    np.write()

while True:
    # Reset LEDs
    gled.value(0)
    rled.value(0)
    yled.value(0)
    # annoyingly, the sensor sees a laser and outputs 0
    laser_signal = not detector.value()
    if laser_signal == 1:  
        builtin_led.value(1)
        gled.value(1)
        yled.value(1)
        print("Laser signal detected!")
        laser.value(1)
    else:
        rled.value(1)
        yled.value(1)
        builtin_led.value(0)
        print("No laser signal.")
        laser.value(0)

    time.sleep(0.1)  
