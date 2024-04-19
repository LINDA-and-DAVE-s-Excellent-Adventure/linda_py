import gc

from utime import sleep_ms, ticks_ms, ticks_diff
from machine import Pin

from libraries.rgbled import WS2812
from libraries.gpio import BUTTON_B_PIN, BUTTON_R_PIN, SWITCH_PIN, LED_PIN
from libraries.linda import Linda

# Pin Setup
led = Pin(LED_PIN, Pin.OUT)
button_B = Pin(BUTTON_B_PIN, Pin.IN, pull=Pin.PULL_DOWN)
button_R = Pin(BUTTON_R_PIN, Pin.IN, pull=Pin.PULL_DOWN)
switch = Pin(SWITCH_PIN, Pin.IN, pull=Pin.PULL_DOWN)

# Disable automatic garbage collection
gc.disable()

# Set up builtin neopixel rgbled with default pins
ws = WS2812()

# Checking for switch changes and button presses
last_B_state = button_B.value()
last_R_state = button_R.value()
last_switch_state = switch.value()
# Debounce handling
debounce_delay_ms = 100
last_B_debounce_time = 0
last_R_debounce_time = 0

# Top-level LINDA object
linda = Linda()
linda.laser._toggle_tx(False)

# Set initial idle state based on toggle switch
idle = bool(switch.value())
active_tx_rx = False

linda.laser.outbox._read_ascii('When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mounth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.')

def check_button_presses() -> None:
    """
    Checks for button presses on Blue and Red buttons, and sets global states accordingly
    """
    global last_B_debounce_time, last_R_debounce_time, active_tx_rx
    current_B_state = button_B.value()
    B_state_changed = current_B_state != last_B_state
    current_R_state = button_R.value()
    R_state_changed = current_R_state != last_R_state
    if B_state_changed:  # Button B pressed
        if current_B_state == 1:
            if ticks_diff(ticks_ms(), last_B_debounce_time) >= debounce_delay_ms:
                last_B_debounce_time = ticks_ms()
                if not idle:
                    linda.laser._toggle_tx(False)
                    active_tx_rx = True
    if R_state_changed: # Button R pressed
        if current_R_state == 1:
            if ticks_diff(ticks_ms(), last_R_debounce_time) >= debounce_delay_ms: 
                last_R_debounce_time = ticks_ms()
                if not idle:
                    linda.laser._toggle_tx(True)
                    active_tx_rx = True

# Main functional loop
# Idle/Active modes are toggled with a hardware switch
# If LINDA is idle, it will cycle through pretty colors on the builtin Neopixel rgbled
#    this also acts as an alignment mode, where the attached LED will illuminate on laser detector activity
# If LINDA is active, it will either transmit or recieve upon Red/Blue button press
#    Red button press will transmit data from the LindaLaser outbox memory buffer
#    Blue button press will start the recieve routine which will capture incoming bits and save the resultant
#        ASCII string to the LindaLaser inbox memory buffer
# At the end of the main loop, check for button presses or mode switch changes, 
#    then run garbage collection and take a short rest
while True:
    if idle:
        linda.laser.laser.on()
        ws.rgb_loop_step()
        # Alignment while in idle mode -- turn builtin LED on when laser is detected
        if not linda.laser.detector.value():
            led.on()
        else:
            led.off()

    else:
        if active_tx_rx:
            if linda.laser.tx_toggle:
                ws.set_color(255,0,0)
                led.on()
                linda.laser.transmit_outbox(64)
                print('done')
                linda.laser._toggle_tx(False)
            else:
                ws.set_color(0,0,255)
                led.on()
                linda.laser.start_rx()
            
            active_tx_rx = False
            ws.set_color(0,255,0)
            led.off()

    # Check for button presses
    check_button_presses()
    # Handle switching of idle state
    if switch.value() != last_switch_state:
        if switch.value():
            idle = True
        else:
            idle = False
            ws.set_color(0,255,0)
        last_switch_state = switch.value()
    gc.collect()
    sleep_ms(5)
