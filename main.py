import machine
import utime
import math
import gc

from utime import sleep_ms
from libraries.laser import LindaLaser

TICK_TIME = 50
PADDING_TIME = 10

# Pin Setup
red_pin = machine.Pin(18, machine.Pin.OUT)
green_pin = machine.Pin(19, machine.Pin.OUT)
blue_pin = machine.Pin(20, machine.Pin.OUT)
button_pin = machine.Pin(12, machine.Pin.IN)
laser_pin = machine.Pin(29, machine.Pin.OUT)

gc.enable()

# Create PWM objects for smooth color transitions
red_pwm = machine.PWM(red_pin)
green_pwm = machine.PWM(green_pin)
blue_pwm = machine.PWM(blue_pin)

# Set PWM frequency (higher frequency = smoother transitions)
red_pwm.freq(1000)
green_pwm.freq(1000)
blue_pwm.freq(1000)

# Helper function to convert color from RGB to PWM duty cycle
def set_color(r, g, b):
    red_pwm.duty_u16(int(r * 65535 / 255))
    green_pwm.duty_u16(int(g * 65535 / 255))
    blue_pwm.duty_u16(int(b * 65535 / 255))

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

inbox = bytearray(64000)
outbox = bytearray(64000)
loiter = memoryview(inbox)[:64]

tl = LindaLaser(loiter, memoryview(inbox), memoryview(outbox))

tl._read_ascii_to_outbox('When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mounth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.', 0)


while True:
    if rainbow_mode:
        # Rainbow color cycle
        for i in range(360):
            angle = i * math.pi / 180
            r = int(127.5 * (math.sin(angle) + 1))
            g = int(127.5 * (math.sin(angle + 2 * math.pi / 3) + 1))
            b = int(127.5 * (math.sin(angle + 4 * math.pi / 3) + 1))
            set_color(r, g, b)
            utime.sleep_ms(5)

            # Check for button press during rainbow cycle
            current_button_state = button_pin.value()
            if current_button_state != last_button_state and current_button_state == 1:  # Button pressed (active low)
                rainbow_mode = False
                last_button_state = current_button_state  # Update button state
                break  # Exit rainbow loop if button is pressed

    else:
        tl.transmit_outbox()
        print("hello!")
        # Solid color cycle
        set_color(255, 0, 0)  # Red
        utime.sleep_ms(1000)
        set_color(0, 255, 0)  # Green
        utime.sleep_ms(1000)
        set_color(0, 0, 255)  # Blue
        utime.sleep_ms(1000)

        # Check for button press during solid color cycle
        current_button_state = button_pin.value()
        if current_button_state != last_button_state and current_button_state == 0:  # Button pressed (active low)
            rainbow_mode = True
            last_button_state = current_button_state  # Update button state

