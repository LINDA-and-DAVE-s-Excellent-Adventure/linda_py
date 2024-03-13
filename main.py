import machine
import utime
import math

from utime import sleep_ms
#from libraries import linda

TICK_TIME = 50
PADDING_TIME = 10

# Pin Setup
red_pin = machine.Pin(18, machine.Pin.OUT)
green_pin = machine.Pin(19, machine.Pin.OUT)
blue_pin = machine.Pin(20, machine.Pin.OUT)
button_pin = machine.Pin(12, machine.Pin.IN)
laser_pin = machine.Pin(29, machine.Pin.OUT)

# Create PWM objects for smooth color transitions
# red_pwm = machine.PWM(red_pin)
# green_pwm = machine.PWM(green_pin)
# blue_pwm = machine.PWM(blue_pin)

# Set PWM frequency (higher frequency = smoother transitions)
# red_pwm.freq(1000)
# green_pwm.freq(1000)
# blue_pwm.freq(1000)

# # Helper function to convert color from RGB to PWM duty cycle
# def set_color(r, g, b):
#     red_pwm.duty_u16(int(r * 65535 / 255))
#     green_pwm.duty_u16(int(g * 65535 / 255))
#     blue_pwm.duty_u16(int(b * 65535 / 255))

def _flash_led(binary_list):
    # set_color(0,0,0)
    for bit in binary_list:
        laser_pin.value(bit)
        red_pin.value(bit)
        sleep_ms(TICK_TIME)

        laser_pin.value(0)
        red_pin.value(0)
        sleep_ms(PADDING_TIME)

def string_to_binary_list(string):
    string_binary = ''.join([f"{ord(letter):08b}" for letter in string])
    bit_list = [int(bit) for bit in string_binary]
    return bit_list

# Main loop for color cycling
last_button_state = button_pin.value()  # Read initial button state
rainbow_mode = True

while True:
    if rainbow_mode:
        # Rainbow color cycle
        for i in range(360):
            angle = i * math.pi / 180
            r = int(127.5 * (math.sin(angle) + 1))
            g = int(127.5 * (math.sin(angle + 2 * math.pi / 3) + 1))
            b = int(127.5 * (math.sin(angle + 4 * math.pi / 3) + 1))
            # set_color(r, g, b)
            utime.sleep_ms(5)

            # Check for button press during rainbow cycle
            current_button_state = button_pin.value()
            if current_button_state != last_button_state and current_button_state == 1:  # Button pressed (active low)
                rainbow_mode = False
                last_button_state = current_button_state  # Update button state
                break  # Exit rainbow loop if button is pressed

    else:
        hello_binary = string_to_binary_list('hello')
        _flash_led(hello_binary)  
        print("hello!")
        # # Solid color cycle
        # set_color(255, 0, 0)  # Red
        # utime.sleep_ms(1000)
        # set_color(0, 255, 0)  # Green
        # utime.sleep_ms(1000)
        # set_color(0, 0, 255)  # Blue
        # utime.sleep_ms(1000)

        # Check for button press during solid color cycle
        current_button_state = button_pin.value()
        if current_button_state != last_button_state and current_button_state == 0:  # Button pressed (active low)
            rainbow_mode = True
            last_button_state = current_button_state  # Update button state

