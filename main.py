import gc
import logging
import sys

from utime import sleep_ms
from machine import Pin

from libraries.rgbled import WS2812
from libraries.gpio import BUTTON_B_PIN, BUTTON_R_PIN, SWITCH_PIN, LED_PIN, DETECTOR_PIN
from libraries.linda import Linda

# Logging setup
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger('linda')
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s")) # type: ignore
log.info('Log configured!')

# Pin Setup
led = Pin(LED_PIN, Pin.OUT)
switch = Pin(SWITCH_PIN, Pin.IN, pull=Pin.PULL_DOWN)
button_B = Pin(BUTTON_B_PIN, Pin.IN, pull=Pin.PULL_DOWN)
button_R = Pin(BUTTON_R_PIN, Pin.IN, pull=Pin.PULL_DOWN)

# Disable automatic garbage collection
gc.disable()

# Set up builtin neopixel rgbled with default pins
ws = WS2812(brightness=16)

# Top-level LINDA object
linda = Linda()
linda.laser._toggle_tx(False)

# Set initial idle state based on toggle switch
idle = bool(switch.value())
active_tx_rx = False

# Moby Dick, by Herman Melville
# Chapter 30: The Pipe
linda.laser.outbox._read_ascii('When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mouth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.')


# Set up interrupt handlers for buttons/switch
def handle_button_R(irq):
    global active_tx_rx
    linda.laser.tx_toggle = True
    active_tx_rx = True

def handle_button_B(irq):
    global active_tx_rx
    linda.laser.tx_toggle = False
    active_tx_rx = True

def toggle_idle(irq):
    global idle
    if switch.value():
        idle = True
    else:
        idle = False
        # ws.set_color(0,255,0)

button_R.irq(handler=handle_button_R, trigger=Pin.IRQ_RISING)
button_B.irq(handler=handle_button_B, trigger=Pin.IRQ_RISING)
switch.irq(handler=toggle_idle, trigger=(Pin.IRQ_FALLING|Pin.IRQ_RISING))

# Main functional loop
# If LINDA is idle, it will cycle through pretty colors on the builtin Neopixel rgbled
#    this also acts as an alignment mode, where the attached LED will illuminate on laser detector activity
# If LINDA is active, it will either transmit or recieve upon Red/Blue button press
#    Red button press will transmit data from the LindaLaser outbox memory buffer
#    Blue button press will start the recieve routine which will capture incoming bits and save the resultant
#        ASCII string to the LindaLaser inbox memory buffer
# At the end of the main loop, run garbage collection and take a short rest
while True:
    linda.laser.laser.on()
    ws.rgb_loop_step()
    # Alignment while idling -- turn builtin LED on when laser is detected
    if not linda.laser.detector.value():
        led.on()
    else:
        led.off()

    if active_tx_rx:
        if linda.laser.tx_toggle:
            print("Transmitting")
            ws.set_color(255,0,0)
            if switch.value():
                linda.laser.transmit_outbox(64)
            linda.laser._toggle_tx(False)
        else:
            print("Receiving")
            ws.set_color(0,0,255)
            linda.laser.start_rx()
        
        active_tx_rx = False

    gc.collect()
    sleep_ms(1)
