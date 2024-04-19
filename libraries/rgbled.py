import machine
import gc
import neopixel
from micropython import const
from gpio import WS2812_PIN
from math import sin, pi

PWM_FREQ = const(10000)
RLED_PIN = const(19)
GLED_PIN = const(18)
BLED_PIN = const(17)

class RGBLED:
    def __init__(self, rpin: int=RLED_PIN, gpin: int=GLED_PIN, bpin: int=BLED_PIN, brightness: int=64) -> None:
        red_pin = machine.Pin(rpin, machine.Pin.OUT)
        green_pin = machine.Pin(gpin, machine.Pin.OUT)
        blue_pin = machine.Pin(bpin, machine.Pin.OUT)
        # Create PWM objects for smooth color transitions
        self.red_pwm = machine.PWM(red_pin)
        self.green_pwm = machine.PWM(green_pin)
        self.blue_pwm = machine.PWM(blue_pin)
        # Set PWM frequency (higher frequency = smoother transitions)
        self.red_pwm.freq(PWM_FREQ)
        self.green_pwm.freq(PWM_FREQ)
        self.blue_pwm.freq(PWM_FREQ)
        # Save brightness modifier (0-256)
        self.brightness = brightness

    def set_color(self, r, g, b):
        self.red_pwm.duty_u16(int(r * 65535 / 255) % self.brightness)
        self.green_pwm.duty_u16(int(g * 65535 / 255) % self.brightness)
        self.blue_pwm.duty_u16(int(b * 65535 / 255) % self.brightness)

    def off(self):
        self.set_color(0,0,0)

class WS2812:
    def __init__(self, pin_num=WS2812_PIN, brightness: int=64):
        """
        Initializes a simple WS2812 LED controller (without PIO)

        Args:
            pin_num (int, optional): The GPIO pin connected to the WS2812 data line. Defaults to 16.
        """
        self.p = machine.Pin(pin_num)
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