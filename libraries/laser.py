from machine import Pin, bitstream, time_pulse_us, disable_irq, enable_irq
from utime import ticks_us, ticks_diff
from micropython import schedule
import gc
import array
import logging
import sys

from memory import InboxBuffer, OutboxBuffer
from gpio import LASER_PIN, DETECTOR_PIN, LED_PIN

# Logging setup
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger('laserlinda')
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s")) # type: ignore
log.info('Laser log configured!')

led = Pin(LED_PIN, Pin.OUT)

gc.disable()

TEST_BITSTREAM = True
# Timing of high-low pulse modulation in machine.bitstream in ns
# (high_time_0, low_time_0, high_time_1, low_time_1)
# (1ms, 3ms, 4ms, 2ms)
# Average bit duration of 5ms -> 200bps data rate
BITSTREAM_TIMING = (1000000, 3000000, 4000000, 2000000)
# BITSTREAM_TIMING = (300000, 700000, 600000, 400000)
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
        self.rx_bits = array.array('i')
        self.rx_chrs = []
        self.tick_dur = 0
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
        if self.rx_flag:
            self.tick_dur = time_pulse_us(self.detector, 0, BITSTREAM_MAX_PULSE_US)
            schedule(self.rx_bits.append, (0 if (abs(self.tick_dur - BITSTREAM_DUR_0) < abs(self.tick_dur - BITSTREAM_DUR_1)) else 1))
            # self.rx_bits.append(0 if (abs(self.tick_dur - BITSTREAM_DUR_0) < abs(self.tick_dur - BITSTREAM_DUR_1)) else 1)

    def _transmit_buffer(self, outbox_mv: memoryview, start_idx: int=0, end_idx: int=32) -> None:
        """
        Transmits data in the given memoryview by bit-banging the laser module output using machine.bitstream()
        Uses high-low pulse duration modulation, defined in the global four-tuple BITSTREAM_TIMING

        Args:
            outbox_mv (memoryview): Memoryview of a bytearray() containing data to transmit
            start_idx (int): Index of memoryview byte to begin transmitting
            end_idx (int): Index of memoryview bytes to end transmitting
        """
        state = disable_irq()
        bitstream(self.laser, 0, BITSTREAM_TIMING, outbox_mv[start_idx:end_idx])
        enable_irq(state)
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
        if msg_len == 0:
            log.info('No message to transmit')
        # Get the length of the outbox message
        elif msg_len == -1:
            log.info(f"Transmitting entire outbox ({len(self.outbox)} bytes)")
            self._transmit_buffer(self.outbox._data, end_idx=len(self.outbox))
        else:
            log.info(f"Transmitting {msg_len} bytes")
            self._transmit_buffer(self.outbox._data, end_idx=msg_len)


    def start_rx(self, duration: int=5):
        """
        Receives laser detector input as data for a given duration. Converts incoming bits to byte integers
        and writes to inbox memory buffer
    
        Args:
            duration (int, optional): Duration to listen, in seconds. Defaults to 5.
        """
        # Sometimes junk data gets in the rx_byte before we start the Rx transaction
        # If that's true, reset self.rx_bits
        if len(self.rx_bits) != 0:
            log.info('Resetting rx_bits')
            self.rx_bits = array.array('i')
        # Reset 
        start = ticks_us()
        self.rx_flag = True
        gc.enable()
        while ticks_diff(ticks_us(), start) < (duration*1000000):
            # Stay in this loop until the Rx transaction has lasted the given duration
            pass
        gc.disable()
        self.rx_flag = False
        gc.collect()
        if len(self.rx_bits) > 0:
            self.decom_rx_bits()
        else:
            log.info("No data was received during Rx period")

    def decom_rx_bits(self):
        """
        Take an array of 1's and 0's, and turn them to an ASCII string to read to the inbox
        """
        log.info("Rx complete, starting decom...")
        rx_str = self.rx_bits_to_str()
        log.info(rx_str)
        gc.collect()
        self.inbox._read_ascii(rx_str)
        self.rx_bits = array.array('i')
        log.info("Rx successful!")
            
    def rx_bits_to_str(self):
        """
        Converts an array of 1's and 0's to 8-bit chars, then combine into a string to return

        Returns:
            _type_: _description_
        """
        byte_string = ""
        for bit in self.rx_bits:
            byte_string += str(bit)
            if len(byte_string) == 8:
                byte_int = int(byte_string, 2)
                self.rx_chrs.append(chr(byte_int))
                byte_string = ""
        return ("".join(self.rx_chrs))
                    
tl = LindaLaser(InboxBuffer(1024), OutboxBuffer(1024))