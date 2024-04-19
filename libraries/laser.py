from machine import Pin, bitstream, time_pulse_us
from utime import ticks_us, ticks_diff
from micropython import const
import gc
import array

from memory import InboxBuffer, OutboxBuffer
from gpio import LASER_PIN, DETECTOR_PIN, SWITCH_PIN

gc.disable()

TEST_BITSTREAM = True
# Timing of high-low pulse modulation in machine.bitstream in ns
# (high_time_0, low_time_0, high_time_1, low_time_1)
# (1ms, 3ms, 4ms, 2ms)
BITSTREAM_TIMING = (1000000, 3000000, 4000000, 2000000)
BITSTREAM_MAX_PULSE_US = int((BITSTREAM_TIMING[2] + BITSTREAM_TIMING[3]) / 1000)
BITSTREAM_DUR_0 = BITSTREAM_TIMING[0]/1000
BITSTREAM_DUR_1 = BITSTREAM_TIMING[2]/1000

class LindaLaser(object):
    def __init__(self, inbox: InboxBuffer, outbox: OutboxBuffer, 
                 laser_pin: int=LASER_PIN, detector_pin: int=DETECTOR_PIN) -> None:
        self.inbox = inbox
        self.outbox = outbox
        self.tx_toggle = True
        self.rx_flag = False
        self.rx_byte = array.array('i')
        # Init the laser and detector pins
        self._init_pins(laser_pin, detector_pin)

    def __repr__(self) -> str:
        return "Laser!"

    def __str__(self) -> str:
        return "Laser"

    def _init_pins(self, laser_pin: int, detector_pin: int) -> None:
        self.laser = Pin(laser_pin, Pin.OUT)
        # The laser sensor modules output LOW when it sees a laser and HIGH otherwise
        self.detector = Pin(detector_pin, Pin.IN, pull=Pin.PULL_UP)
        self.detector.irq(handler=self._rx_bitstream, trigger=Pin.IRQ_FALLING)
        # Switch for debugging
        self.switch = Pin(SWITCH_PIN, Pin.IN)

    def _toggle_tx(self, tx_toggle: bool) -> None:
        """
        Update the global LindaLaser state to toggle between Tx and Rx

        Args:
            tx_toggle (bool): State toggle boolean. TRUE if Tx, FALSE if Rx
        """
        self.tx_toggle = tx_toggle

    def _rx_bitstream(self, irq):
        """
        Callback function triggered on laser detector interrupt. 
        If receiving, time the incoming tick and save its duration to the rx_byte array

        Args:
            irq (irq): Default single-argument of micropython interrupt callbacks
        """
        tick_dur = time_pulse_us(self.detector, 0, BITSTREAM_MAX_PULSE_US)
        if self.rx_flag:
            # rx_bit_val = 0 if (abs(tick_dur - BITSTREAM_DUR_0) < abs(tick_dur - BITSTREAM_DUR_1)) else 1
            self.rx_byte.append(0 if (abs(tick_dur - BITSTREAM_DUR_0) < abs(tick_dur - BITSTREAM_DUR_1)) else 1)

    def _transmit_buffer(self, outbox_mv: memoryview, start_idx: int=0, end_idx: int=32) -> None:
        """
        Transmits data in the given memoryview by bit-banging the laser module output using machine.bitstream()
        Uses high-low pulse duration modulation, defined in the global four-tuple BITSTREAM_TIMING

        Args:
            outbox_mv (memoryview): Memoryview of a bytearray() containing data to transmit
            start_idx (int): Index of memoryview byte to begin transmitting
            end_idx (int): Index of memoryview bytes to end transmitting
        """
        bitstream(self.laser, 0, BITSTREAM_TIMING, outbox_mv[start_idx:end_idx])
        gc.collect()
        self.laser.off()

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

    def start_rx(self, duration: int=5):
        """
        Recieves laser detector input as data for a given duration. Converts incoming bits to byte integers
        and writes to inbox memory buffer
    
        Args:
            duration (int, optional): Duration to listen, in seconds. Defaults to 5.
        """
        rx_byte = int()
        self.rx_flag = True
        start = ticks_us()
        while ticks_diff(ticks_us(), start) < (duration*1000000):
            if len(self.rx_byte) == 8:
                rx_byte = int("".join(str(bit) for bit in self.rx_byte), 2)
                self.inbox.rx_byte(rx_byte)
                self.rx_byte = array.array('i')
                print(rx_byte, chr(rx_byte))
        gc.collect()


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
                self.rx_flag = True
                while not self.tx_toggle:
                    if len(self.rx_byte) == 8:
                        rx_byte = int("".join(str(bit) for bit in self.rx_byte), 2)
                        self.inbox.rx_byte(rx_byte)
                        self.rx_byte = array.array('i')
                        print(rx_byte, chr(rx_byte))
                    
tl = LindaLaser(InboxBuffer(1024), OutboxBuffer(1024))
tl.tx_toggle = False
tl.rx_flag = True
tl.laser.on()
g = Pin(18, Pin.OUT)
r = Pin(19, Pin.OUT)

rx_byte = array.array('i')
rx_next_bit = -1
rising = False

def toggle_g(t):
    g.value(not g.value())


test = bytearray('hello world!'.encode())

det = Pin(20, Pin.IN, pull=Pin.PULL_UP)
bitstream_max_pulse = int((BITSTREAM_TIMING[2] + BITSTREAM_TIMING[3]) / 1000)

def bitstream_dur(t):
    tick_dur = time_pulse_us(det, 0, bitstream_max_pulse)
    rx_byte.append(1 if (abs(tick_dur - BITSTREAM_DUR_0) < abs(tick_dur - BITSTREAM_DUR_1)) else 0)

det.irq(handler=bitstream_dur, trigger=Pin.IRQ_FALLING)



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
        if bit == -1: 
            break
        elif bit not in (0, 1):
            raise ValueError("Bit array contains invalid values. Only 0 and 1 are allowed.")

        current_byte = (current_byte << 1) | bit
        bit_index += 1

        if bit_index == 8:
            characters.append(chr(current_byte))
            current_byte = 0
            bit_index = 0

    return characters

def rx_byte_string(bit_list):
    chrs = []
    byte_string = ""
    for bit in bit_list:
        byte_string += str(bit)
        if len(byte_string) == 8:
            byte_int = int(byte_string, 2)
            chrs.append(chr(byte_int))
            byte_string = ""

    if byte_string:
        print("oops too long")

    return chrs

def print_rx_byte(bit_list):
    chrs = rx_byte_string(bit_list)
    print("".join(chrs))

def print_inbox_msg():
    for chrint in tl.inbox._data:
        print(chr(chrint))