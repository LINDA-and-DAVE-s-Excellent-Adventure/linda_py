import neopixel
from machine import Pin
from gpio import WS2812_PIN
from math import sin, pi

class WS2812:
    def __init__(self, pin_num=WS2812_PIN, brightness: int=64):
        """
        Initializes a simple WS2812 LED controller (without PIO)

        Args:
            pin_num (int, optional): The GPIO pin connected to the WS2812 data line. Defaults to 16.
        """
        self.p = Pin(pin_num, pull=Pin.PULL_DOWN)
        self.np = neopixel.NeoPixel(self.p, 1) # type: ignore
        self.brightness = brightness
        self.color_wheel_angle = 0
        self.color_wheel_rad = 0
        self.r_wheel = 0
        self.g_wheel = 0
        self.b_wheel = 0

    def set_color(self, r, g, b):
        self.np[0] = (r%self.brightness, g%self.brightness, b%self.brightness) # type: ignore
        self.np.write()

    def on(self):
        self.set_color(255,255,255)

    def off(self):
        self.set_color(0,0,0)

    def rgb_loop_step(self):
        self.color_wheel_angle += 0.1
        self.color_wheel_angle %= 360 
        self.color_wheel_rad = self.color_wheel_angle * pi / 180

        self.r_wheel = int(127.5 * (sin(self.color_wheel_rad) + 1))
        self.g_wheel = int(127.5 * (sin(self.color_wheel_rad + 2 * pi / 3) + 1))
        self.b_wheel = int(127.5 * (sin(self.color_wheel_rad + 4 * pi / 3) + 1))

        self.set_color(self.r_wheel,self.g_wheel,self.b_wheel)
