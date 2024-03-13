from machine import Pin
from utime import sleep_us, ticks_us, sleep_ms, ticks_ms
from time import sleep
from sys import stdout
import struct

# Testing on Thing Plus
# RLED_PIN = 21
# GLED_PIN = 19
# DETECTOR_PIN = 16
# LASER_PIN = 25
# SWITCH_PIN = 18

# Testing on WeAct RP2040
RLED_PIN = 18
GLED_PIN = 19
BLED_PIN = 20
SWITCH_PIN = 12
LASER_PIN = 29
DETECTOR_PIN = 7

TICK_TIME = 25
PADDING_TIME = 25

TICK_DURATION_MS = 3
TICK_THRESHOLD_MS = 2

TX_RX_STATE = False
RECORDING = False

led = Pin(RLED_PIN, Pin.OUT)
laser = Pin(LASER_PIN, Pin.OUT)
switch = Pin(SWITCH_PIN, Pin.IN)
detector = Pin(DETECTOR_PIN, Pin.IN)
green = Pin(GLED_PIN, Pin.OUT)

class LindaLaser:
    def __init__(self, loiter_mv: memoryview, inbox_mv: memoryview, outbox_mv: memoryview, 
                 laser_pin: int, detector_pin: int) -> None:
        self.loiter = loiter_mv
        self.inbox = inbox_mv
        self.outbox = outbox_mv
        self._init_pins(laser_pin, detector_pin)

    def __repr__(self) -> str:
        return "Laser!"

    def __str__(self) -> str:
        return "Laser"

    def _init_pins(self, laser_pin: int, detector_pin: int) -> None:
        self.laser = Pin(laser_pin, Pin.OUT)
        self.detector = Pin(detector_pin, Pin.IN)

    def _print_outbox(self, chunk_size: int=256) -> None:
        start = 0
        while start < len(self.outbox):
            chunk = self.outbox[start: start+chunk_size]
            decoded_chunk = bytes(chunk).decode('ascii')
            stdout.write(decoded_chunk)
        start += chunk_size

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
        for byte in outbox_mv[start_idx:end_idx]:
            print(f"{chr(byte)}")
            for i in range(7, -1, -1):
                # Extract the bit value
                led.value((byte >> i) & 1)
                self.laser.value((byte >> i) & 1)
                sleep_ms(TICK_TIME)
            sleep_ms(PADDING_TIME)

    def _receive(self, loiter_mv: memoryview, inbox_mv: memoryview) -> None:
        print("listening")

    def transmit_outbox(self) -> None:
        """
        Transmit the contents of self.outbox
        """
        print(f"Transmitting: {self.outbox}")
        self._transmit(self.outbox)

    def read_ascii_to_outbox(self, msg: str, idx: int) -> None:
        for i, char in enumerate(msg):
            if idx+i >= len(self.outbox):
                break
            self.outbox[idx+i] = ord(char)

    def start(self) -> None:
        print("Starting Laser loop")

def flash_led_bytearray(array: bytearray):
    for byte in array:
        for bit in bin(byte)[2:]:
            led.value(int(bit))
            laser.value(int(bit))
            sleep_us(TICK_TIME)

            led.value(0)
            laser.value(0)
            sleep_us(PADDING_TIME)

def listen_tick():
    start_time = ticks_us()
    while ticks_us() - start_time < TICK_DURATION_MS:
        if not detector.value() == 1:
            led.value(1)
            if ticks_us() - start_time >= TICK_THRESHOLD_MS:
                print("Laser detected for at least 2ms")
                break
        else:
            led.value(0)
        sleep_us(1)

def blink_led():
    for _ in range(5):
        led.value(1)
        laser.value(1)
        sleep_ms(500)
        led.value(0)
        laser.value(0)
        sleep_ms(500)

inbox = bytearray(64000)
outbox = bytearray(64000)
loiter = memoryview(inbox)[:64]

test_linda = LindaLaser(memoryview(loiter), memoryview(inbox), memoryview(outbox), 
                        LASER_PIN, DETECTOR_PIN)

test_linda.read_ascii_to_outbox('When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mounth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.', 0)