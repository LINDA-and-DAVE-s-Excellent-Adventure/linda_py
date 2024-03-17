from machine import Pin, mem32
from utime import sleep_ms
import utime
import rp2
import gc
import errno

from memory import InboxBuffer, OutboxBuffer

# Testing on Thing Plus
RLED_PIN = 19
GLED_PIN = 18
BLED_PIN = 17
DETECTOR_PIN = 20
LASER_PIN = 21
BUTTON_PIN = 22

# # Testing on WeAct RP2040
# RLED_PIN = 18
# GLED_PIN = 19
# BLED_PIN = 20
# DETECTOR_PIN = 7
# LASER_PIN = 29
# BUTTON_PIN = 12

PIO_FREQ_HZ = 2000
TICK_TIME = 7
PADDING_TIME = 3

TICK_DURATION_MS = 20
TICK_THRESHOLD_MS = 10

TX_RX_STATE = False
RECORDING = False

rled = Pin(RLED_PIN, Pin.OUT)
gled = Pin(GLED_PIN, Pin.OUT)
bled = Pin(BLED_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN)
class LindaLaser:
    def __init__(self, inbox: InboxBuffer, outbox: OutboxBuffer, 
                 laser_pin: int=LASER_PIN, detector_pin: int=DETECTOR_PIN) -> None:
        self.inbox = inbox
        self.outbox = outbox
        self._init_pins(laser_pin, detector_pin)

    def __repr__(self) -> str:
        return "Laser!"

    def __str__(self) -> str:
        return "Laser"

    def _init_pins(self, laser_pin: int, detector_pin: int) -> None:
        self.laser = Pin(laser_pin, Pin.OUT)
        # self.detector = Pin(detector_pin, Pin.IN)

    def _toggle_tx(self, tx_toggle: bool) -> None:
        """
        Update the global LindaLaser state to toggle between Tx and Rx

        Args:
            tx_toggle (bool): State toggle boolean. TRUE if Tx, FALSE if Rx
        """
        TX_RX_STATE = tx_toggle

    def _transmit(self, outbox_mv: memoryview, start_idx: int=0, end_idx: int=32) -> None:
        """
        Blinks the bitwise contents in the given range for the provided memoryview, 
            using the Laser and/or LED

        Args:
            outbox_mv (memoryview): Memoryview of a bytearray() containing data to transmit
        """
        print(f"Transmitting {end_idx-start_idx} bytes! Should take {(end_idx-start_idx)*8*(TICK_TIME) / 1000:.2f} seconds")
        rled.value(0)
        bled.value(0)
        gled.value(0)
        gc.collect()
        start_time = utime.ticks_ms()
        for byte_idx in range(start_idx,end_idx):
            current_byte = outbox_mv[byte_idx]
            print(chr(current_byte), end='')
            for i in range(7, -1, -1):
                try: 
                    # Extract the bit value
                    bit = (current_byte >> i) & 1
                    rled.value(bit)
                    self.laser.value(bit)
                    sleep_ms(TICK_TIME)
                except IOError as e:
                    if e.errno == errno.EIO:
                        print("Had that weird input error")
        end_time = utime.ticks_ms()
        elapsed_time = utime.ticks_diff(end_time, start_time)
        print(f"\nActual transmit duration: {elapsed_time/1000} ms")
        gc.collect()
        rled.value(0)
        # self.laser.value(0)
        gled.value(1)

    def _receive(self, loiter_mv: memoryview, inbox_mv: memoryview) -> None:
        print("listening")

    def transmit_outbox(self) -> None:
        """
        Transmit the contents of self.outbox
        """
        self._transmit(self.outbox.msg, end_idx=256)

    def start(self) -> None:
        print("Starting Laser loop")

    def blink_led(self):
        for _ in range(1):
            gled.value(0)
            bled.value(0)
            rled.value(1)
            self.laser.value(1)
            # sm.exec("set(pins, 1)")
            sleep_ms(500)
            rled.value(0)
            bled.value(0)
            gled.value(1)
            sleep_ms(500)
            rled.value(0)
            gled.value(0)
            bled.value(1)
            self.laser.value(0)
            # sm.exec("set(pins, 0)")
            sleep_ms(500)
        rled.value(0)
        gled.value(0)
        bled.value(0)

# def listen_tick():
#     start_time = ticks_us()
#     while ticks_us() - start_time < TICK_DURATION_MS:
#         if not detector.value() == 1:
#             rled.value(1)
#             if ticks_us() - start_time >= TICK_THRESHOLD_MS:
#                 print("Laser detected for at least 2ms")
#                 break
#         else:
#             rled.value(0)
#         sleep_us(1)

inbox = InboxBuffer(64000)
outbox = OutboxBuffer(64000)

tl = LindaLaser(inbox, outbox, LASER_PIN, DETECTOR_PIN)

tl.outbox._read_ascii('When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mounth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.')

gc.disable()

tl.blink_led()
