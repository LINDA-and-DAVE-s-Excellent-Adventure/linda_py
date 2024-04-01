from machine import Pin, Signal
from utime import sleep_us, sleep_us, ticks_us, ticks_us, ticks_diff
from micropython import const
import gc

from memory import InboxBuffer, OutboxBuffer
from gpio import LASER_PIN, DETECTOR_PIN

# Duration laser will be on/off for a 1/0 bit during transmission
# 5ms = 5000us
LASER_TICK_TIME_US = const(5000)
# While idling, check for input every 0.25ms
IDLE_TICK_TIME_US = const(250)

# Transmit 0xffff to signal message start
MSG_BEGIN = bytearray(bytes([0xff, 0xff]))
# Transmit 0xdead to signal message end
MSG_END = bytearray(bytes([0xde, 0xad]))
# Duration of MSG_BEGIN transmission is (LASER_TICK_TIME_US * 16 bits) ms
MSG_BEGIN_DURATION_US = LASER_TICK_TIME_US * 16

# Keep the start time of a Rx transmission globally
RX_START_TIME = None

class LindaLaser:
    def __init__(self, inbox: InboxBuffer, outbox: OutboxBuffer, 
                 laser_pin: int=LASER_PIN, detector_pin: int=DETECTOR_PIN) -> None:
        self.inbox = inbox
        self.outbox = outbox
        self.tx_toggle = True
        self._init_pins(laser_pin, detector_pin)

    def __repr__(self) -> str:
        return "Laser!"

    def __str__(self) -> str:
        return "Laser"

    def _init_pins(self, laser_pin: int, detector_pin: int) -> None:
        self.laser = Pin(laser_pin, Pin.OUT)
        # The laser sensor modules output LOW when it sees a laser and HIGH otherwise, so invert it
        self.detector = Signal(detector_pin, Pin.IN, invert=True)

    def _toggle_tx(self, tx_toggle: bool) -> None:
        """
        Update the global LindaLaser state to toggle between Tx and Rx

        Args:
            tx_toggle (bool): State toggle boolean. TRUE if Tx, FALSE if Rx
        """
        self.tx_toggle = tx_toggle

    def _transmit_byte(self, byte: int) -> None:
        """
        Given an integer, blink it bitwise. Will only blink 8 bits, could be configured to take argument for larger ints

        Args:
            byte (int): Integer to transmit
        """
        print(chr(byte), end='')
        for i in range(7, -1, -1):
            # Extract the bit value
            bit = (byte >> i) & 1
            self.laser.value(bit)
            sleep_us(LASER_TICK_TIME_US)

    def _transmit_buffer(self, outbox_mv: memoryview, start_idx: int=0, end_idx: int=32, linda_header=True, linda_trailer = True) -> None:
        """
        Blinks the bitwise contents in the given range for the provided memoryview, 
            using the Laser and/or LED

        Args:
            outbox_mv (memoryview): Memoryview of a bytearray() containing data to transmit
            start_idx (int): Index of memoryview byte to begin transmitting
            end_idx (int): Index of memoryview bytes to end transmitting
        """
        gc.collect()
        if linda_header:
            # Transmit 0xffff to signal beginning of message
            self._transmit_byte(MSG_BEGIN[0])
            self._transmit_byte(MSG_BEGIN[1])
        print(f"Transmitting {end_idx-start_idx} bytes.\nEstimated: {(end_idx-start_idx)*8*(LASER_TICK_TIME_US) / 1000000:.2f} seconds")
        start_time = ticks_us()
        for byte_idx in range(start_idx,end_idx):
            current_byte = outbox_mv[byte_idx]
            self._transmit_byte(current_byte)
        end_time = ticks_us()
        elapsed_time = ticks_diff(end_time, start_time)
        print(f"\nActual: {elapsed_time/1000} ms")
        if linda_trailer:
            # Transmit 0xdead to signal end of message
            self._transmit_byte(MSG_END[0])
            self._transmit_byte(MSG_END[1])
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

    def _listen_tick(self, detection_mode=False) -> int: 
        """
        Listens for one LASER_TICK_TIME_US duration, and returns the integer value of detector signal during
          that tick

        Returns:
            int: Integer 1 or 0 of whether the detector saw a laser during this tick
        """
        start_time = ticks_us()
        tick_val = self.detector.value()
        if detection_mode:
            if tick_val == 1:
                global RX_START_TIME
                if RX_START_TIME is None:
                    RX_START_TIME = ticks_us()
                elif ticks_us() - RX_START_TIME >= MSG_BEGIN_DURATION_US:
                    self.inbox.set_recording(True)
                    RX_START_TIME = None
                    print("NOW RECORDING!")
                    return tick_val
        else:
            # Loop and wait for a whole laser tick, setting the tick_val continuously
            while(ticks_diff(ticks_us(), start_time) < LASER_TICK_TIME_US):
                tick_val = self.detector.value()

        return tick_val

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
                rx_bits = []
                while not self.tx_toggle:
                    if self.inbox.recording:
                        rx_bits.append(self._listen_tick())
                        if len(rx_bits) == 8:
                            rx_byte = int("".join(str(bit) for bit in rx_bits), 2)
                            self.inbox.rx_byte(rx_byte)
                            rx_bits.clear()
                            print(f"Rx byte: {rx_byte} {chr(rx_byte)}")
                    else:
                        print("Detecting...")
                        self._listen_tick(detection_mode=True)

                        sleep_us(IDLE_TICK_TIME_US)

                    
tl = LindaLaser(InboxBuffer(1024), OutboxBuffer(1024))
tl.tx_toggle = False

# def test_1_sec():
#     tv = 0
#     start_time = ticks_us()
#     print("Start")
#     while(ticks_diff(ticks_us(), start_time) < 1000000):
#         pass
#     duration = ticks_diff(ticks_us(), start_time)/1000000
#     print(f"Done: {duration} s")
#     return duration

# durations = []
# for i in range(120):
#     print(f"{i}: ")
#     durations.append(test_1_sec())
# print(sum(durations)/120)