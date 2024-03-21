import machine
import neopixel
from gpio import RLED_PIN, GLED_PIN, BLED_PIN, WS2812_PIN

PWM_FREQ = 10000

class RGBLED:
    def __init__(self, rpin: int=RLED_PIN, gpin: int=GLED_PIN, bpin: int=BLED_PIN) -> None:
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

    def set_color(self, r, g, b):
        self.red_pwm.duty_u16(int(r * 65535 / 255))
        self.green_pwm.duty_u16(int(g * 65535 / 255))
        self.blue_pwm.duty_u16(int(b * 65535 / 255))

    def off(self):
        self.set_color(0,0,0)

class WS2812:
    def __init__(self, pin_num=WS2812_PIN):
        """
        Initializes a simple WS2812 LED controller (without PIO)

        Args:
            pin_num (int, optional): The GPIO pin connected to the WS2812 data line. Defaults to 16.
        """
        self.p = machine.Pin(pin_num)
        self.np = neopixel.NeoPixel(self.p, 1) # type: ignore

    def set_color(self, r, g, b):
        self.np[0] = (r, g, b)
        self.np.write()

