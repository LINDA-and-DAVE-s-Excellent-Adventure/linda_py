from machine import Pin, Signal, Timer
from utime import sleep_us, sleep_us, ticks_us, ticks_us, ticks_diff
from micropython import const, alloc_emergency_exception_buf, schedule
import gc
import array

from memory import InboxBuffer, OutboxBuffer
from gpio import LASER_PIN, DETECTOR_PIN

# Duration laser will be on/off for a 1/0 bit during transmission
# 5ms = 5000us
LASER_TICK_TIME_US = const(5000)
# While idling, check for input every 0.25ms
IDLE_TICK_TIME_US = const(250)
# Set the frequency of Tx/Rx timers dynamically
LASER_TICK_FREQUENCY = int(1000000 / LASER_TICK_TIME_US)

# Transmit 0xffff to signal message start
MSG_BEGIN = bytearray(bytes([0xff, 0xff]))
# Transmit 0xdead to signal message end
MSG_END = bytearray(bytes([0xde, 0xad]))
# Duration of MSG_BEGIN transmission is (LASER_TICK_TIME_US * 16 bits) ms
MSG_BEGIN_DURATION_US = LASER_TICK_TIME_US * 16

# Keep the start time of a Rx transmission globally
RX_START_TIME = None

# Set up micropython interrupt logic & place to store incoming bits
alloc_emergency_exception_buf(100)

class LindaLaser(object):
    def __init__(self, inbox: InboxBuffer, outbox: OutboxBuffer, 
                 laser_pin: int=LASER_PIN, detector_pin: int=DETECTOR_PIN) -> None:
        self.inbox = inbox
        self.outbox = outbox
        self.tx_toggle = True
        # Set up the timer to handle Rx timing, will be init'd when needed
        self.rx_timer = Timer(-1)
        self.stop_rx_timer = Timer(-1)
        self.rx_byte = array.array('i')
        self.rx_tick_ref = self._rx_tick
        # Set up timer to handle Tx timing
        self.tx_timer = Timer(-1)
        self.tx_next_bit = 0
        self.tx_tick_ref = self._tx_tick
        self._init_pins(laser_pin, detector_pin)

    def __repr__(self) -> str:
        return "Laser!"

    def __str__(self) -> str:
        return "Laser"

    def _init_pins(self, laser_pin: int, detector_pin: int) -> None:
        self.laser = Pin(laser_pin, Pin.OUT)
        # The laser sensor modules output LOW when it sees a laser and HIGH otherwise
        self.detector = Pin(detector_pin, Pin.IN)
        self.detector.irq(handler=self._trigger_rx_start, trigger=Pin.IRQ_FALLING)

    def _toggle_tx(self, tx_toggle: bool) -> None:
        """
        Update the global LindaLaser state to toggle between Tx and Rx

        Args:
            tx_toggle (bool): State toggle boolean. TRUE if Tx, FALSE if Rx
        """
        self.tx_toggle = tx_toggle

    def _trigger_rx_start(self, timer):
        self._init_rx_timer(dur=1000)

    def _init_rx_timer(self, dur=5000):
        """
        Init the Rx timer, along with a one-shot after [dur] milliseconds to disable

        Args:
            dur (int, optional): Millisecond duration to wait before disabling Rx timer. Defaults to 5000 (5 seconds).
        """
        self.rx_timer.init(freq=LASER_TICK_FREQUENCY, mode=Timer.PERIODIC, callback=self._rx_tick)
        self.stop_rx_timer.init(period=dur, mode=Timer.ONE_SHOT, callback=lambda t: self.rx_timer.deinit())

    def _init_tx_timer(self):
        self.tx_timer.init(freq=LASER_TICK_FREQUENCY, mode=Timer.PERIODIC, callback=self.tx_tick_ref)

    def _deinit_tx_timer(self):
        self.tx_timer.deinit()

    def _rx_tick(self, timer) -> None:
        self.rx_byte.append(not self.detector.value())

    def _tx_tick(self, timer) -> None:
        self.laser.value(self.tx_next_bit)

    def _transmit_byte(self, byte: int) -> None:
        """
        Given an integer, blink it bitwise. Will only blink 8 bits, could be configured to take argument for larger ints

        Args:
            byte (int): Integer to transmit
        """
        # print(chr(byte), end='')
        sleep_dur = int(LASER_TICK_TIME_US/2)
        for i in range(7, -1, -1):
            # Extract the bit value
            bit = (byte >> i) & 1
            self.tx_next_bit = bit
            sleep_us(sleep_dur)

    def _transmit_buffer(self, outbox_mv: memoryview, start_idx: int=0, end_idx: int=32, linda_header=True, linda_trailer = True) -> None:
        """
        Blinks the bitwise contents in the given range for the provided memoryview, 
            using the Laser and/or LED

        Args:
            outbox_mv (memoryview): Memoryview of a bytearray() containing data to transmit
            start_idx (int): Index of memoryview byte to begin transmitting
            end_idx (int): Index of memoryview bytes to end transmitting
        """
        self.laser.value(1)
        gc.collect()
        self._init_tx_timer()
        if linda_header:
            # Transmit 0xffff to signal beginning of message
            self._transmit_byte(MSG_BEGIN[0])
            self._transmit_byte(MSG_BEGIN[1])
        for byte in outbox_mv[start_idx:end_idx]:
            self._transmit_byte(byte)
        if linda_trailer:
            # Transmit 0xdead to signal end of message
            self._transmit_byte(MSG_END[0])
            self._transmit_byte(MSG_END[1])
        self._deinit_tx_timer()
        gc.collect()
        self.laser.value(0)

    def transmit_outbox(self, msg_len: int=-1) -> None:
        """
        Transmit the contents of the outbox, optionally choosing the amount of data to transmit.
        If no length argument is given, transmit the entire message

        Args:
            msg_len (int, optional): The length in bytes of the message to send. Defaults to -1,
                which indicates transmission of the entire outbox message.
        """
        # Get the length of the outbox message
        if msg_len == -1:
            self._transmit_buffer(self.outbox._msg, end_idx=len(self.outbox))
        else:
            self._transmit_buffer(self.outbox._msg, end_idx=msg_len)

    def _idle_tick(self) -> None:
        """
        Listens for one LASER_TICK_TIME_US duration, and returns the integer value of detector signal during
          that tick
        """
        if self.detector.value() == 0:
            global RX_START_TIME
            if RX_START_TIME is None:
                RX_START_TIME = ticks_us()
            else:
                while self.detector.value() == 0:
                    if (ticks_diff(ticks_us(), RX_START_TIME) >= MSG_BEGIN_DURATION_US):
                        self.inbox.set_recording(True)
                        self._init_rx_timer(dur=2000)
                        RX_START_TIME = None

    def start(self) -> None:
        print("Starting Laser loop")
        gc.collect()
        while True:
            if self.tx_toggle:
                # Transmitting
                if self.outbox:
                    print("Outbox message is ready for transmit!")
                    self.transmit_outbox()
                else:
                    # Message isn't ready -- loop again
                    continue
            else:
                # Receiving
                while not self.tx_toggle:
                    if self.inbox.recording:
                        if len(self.rx_byte) == 8:
                            rx_byte = int("".join(str(bit) for bit in self.rx_byte), 2)
                            self.inbox.rx_byte(rx_byte)
                            self.rx_byte = array.array('i')
                            print(rx_byte, chr(rx_byte))
                    else:
                        self._idle_tick()
                        # sleep_us(IDLE_TICK_TIME_US)

                    
tl = LindaLaser(InboxBuffer(1024), OutboxBuffer(1024))
tl.tx_toggle = False
tl.outbox._read_ascii('hello world!')
tl.laser.on()
g = Pin(18, Pin.OUT)
r = Pin(19, Pin.OUT)

tim = Timer(-1)
dl = Timer(-1)

def toggle_g(t):
    g.value(not g.value())

def disable_g_timer(t):
    tim.deinit()

# rx_byte = array.array('i')
def rx_start(t):
    tl._init_rx_timer(dur=2000)

# tl.detector.irq(handler=rx_start, trigger=Pin.IRQ_FALLING)

def bits_to_chars(bit_array):
    """Converts an array of bits (0s and 1s) to characters, padding with 0s if necessary.

    Args:
        bit_array (list): A list of integers (0 or 1) representing the bits.

    Returns:
        list: A list of characters resulting from the conversion.
    """

    characters = []
    current_byte = 0
    bit_index = 0

    # Padding if necessary
    while len(bit_array) % 8 != 0:
        bit_array.append(0)  

    for bit in bit_array:
        if bit not in (0, 1):
            raise ValueError("Bit array contains invalid values. Only 0 and 1 are allowed.")

        current_byte = (current_byte << 1) | bit
        bit_index += 1

        if bit_index == 8:
            characters.append(chr(current_byte))
            current_byte = 0
            bit_index = 0

    return characters

def print_rx_byte(rx_byte):
    chrs = bits_to_chars(rx_byte)
    for chr in chrs:
        print(chr)

# tim.init(freq=2, mode=Timer.PERIODIC, callback=toggle_g)