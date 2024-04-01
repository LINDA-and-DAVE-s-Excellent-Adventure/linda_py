import machine
import gc

from math import sin, pi
from utime import sleep_ms
from libraries.rgbled import RGBLED, WS2812
from libraries.gpio import BUTTON_PIN, SWITCH_PIN, DETECTOR_PIN, LASER_PIN
from libraries.linda import Linda

# Pin Setup
button = machine.Pin(BUTTON_PIN, machine.Pin.IN)
switch = machine.Pin(SWITCH_PIN, machine.Pin.IN)
detector = machine.Pin(DETECTOR_PIN, machine.Pin.IN)
laser = machine.Pin(LASER_PIN, machine.Pin.OUT)

gc.disable()

# Set up rgbled with default pins
rgb = RGBLED()
ws = WS2812()

# Main loop for color cycling
last_button_state = button.value() # Read initial button state
rainbow_mode = True

tl = Linda()

tl.laser.outbox._read_ascii('When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mounth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.')

while True:
    if switch.value():
        laser.value(1)
        rgb.set_color(0,255,0)
        ws.set_color(0,0,0)
        if detector.value() == 0:
            print("laser!")
            ws.set_color(255, 255, 255)
            rgb.set_color(255,0,0)
        else:
            print("no laser!")     
    else: 
        if rainbow_mode:
            # Rainbow color cycle
            for i in range(360):
                if detector.value():
                    ws.set_color(255, 0, 0)
                else: 
                    angle = i * pi / 180
                    r = int(127.5 * (sin(angle) + 1))
                    g = int(127.5 * (sin(angle + 2 * pi / 3) + 1))
                    b = int(127.5 * (sin(angle + 4 * pi / 3) + 1))
                    rgb.set_color(r, g, b)
                    ws.set_color(r, g, b)
                sleep_ms(5)

                # Check for button press during rainbow cycle
                current_button_state = button.value()
                if current_button_state != last_button_state and current_button_state == 1:  # Button pressed (active low)
                    rainbow_mode = False
                    last_button_state = current_button_state  # Update button state
                    break  # Exit rainbow loop if button is pressed
                gc.collect()

        else:
            rgb.set_color(255,0,0)
            print(tl.laser.tx_toggle)
            tl.laser.transmit_outbox(64)
            tl.laser._toggle_tx(False)
            # Solid color cycle
            rgb.set_color(255, 0, 0)  # Red
            sleep_ms(500)
            rgb.set_color(0, 255, 0)  # Green
            sleep_ms(500)
            rgb.set_color(0, 0, 255)  # Blue
            sleep_ms(500)
            rgb.off()
            sleep_ms(500)

            # Check for button press during solid color cycle
            current_button_state = button.value()
            if current_button_state != last_button_state and current_button_state == 0:  # Button pressed (active low)
                rainbow_mode = True
                last_button_state = current_button_state  # Update button state
    gc.collect()
