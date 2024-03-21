from machine import Pin
from utime import sleep_ms, ticks_ms, ticks_diff
from micropython import const
import gc

from memory import InboxBuffer, OutboxBuffer
from gpio import LASER_PIN, DETECTOR_PIN

TICK_TIME_MS = const(5)
TICK_THRESHOLD_MS = const(3)
PADDING_TIME_MS = const(2)

START_MARKER = const(0xBEEF)
END_MARKER = const(0xDEAD)
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
        self.detector = Pin(detector_pin, Pin.IN)

    def _toggle_tx(self, tx_toggle: bool) -> None:
        """
        Update the global LindaLaser state to toggle between Tx and Rx

        Args:
            tx_toggle (bool): State toggle boolean. TRUE if Tx, FALSE if Rx
        """
        self.tx_toggle = tx_toggle

    def _transmit(self, outbox_mv: memoryview, start_idx: int=0, end_idx: int=32) -> None:
        """
        Blinks the bitwise contents in the given range for the provided memoryview, 
            using the Laser and/or LED

        Args:
            outbox_mv (memoryview): Memoryview of a bytearray() containing data to transmit
        """
        print(f"Transmitting {end_idx-start_idx} bytes! Should take {(end_idx-start_idx)*8*(TICK_TIME_MS) / 1000:.2f} seconds")
        gc.collect()
        start_time = ticks_ms()
        for byte_idx in range(start_idx,end_idx):
            current_byte = outbox_mv[byte_idx]
            print(chr(current_byte), end='')
            for i in range(7, -1, -1):
                # Extract the bit value
                bit = (current_byte >> i) & 1
                self.laser.value(bit)
                sleep_ms(TICK_TIME_MS)
        end_time = ticks_ms()
        elapsed_time = ticks_diff(end_time, start_time)
        print(f"\nActual transmit duration: {elapsed_time/1000} ms")
        gc.collect()
        self.laser.value(0)

    def _receive(self, loiter_mv: memoryview, inbox_mv: memoryview) -> None:
        print("listening")
        received_bits = []
        last_read_time = ticks_ms()
        while not self.tx_toggle:
            print('tick')
            sleep_ms(PADDING_TIME_MS)
            detector_state = self.detector.value()
            bit_value = 1 if ticks_ms() - last_read_time >= TICK_THRESHOLD_MS else 0
            last_read_time = ticks_ms()
            received_bits.append(bit_value)

            if len(received_bits) == 8:
                word = 0
                for i in range(8):
                    word <<= i  # Shift existing bits
                    word |= received_bits.pop(0)  # Add the next bit

                if word == START_MARKER:
                    recording = True
                elif word == END_MARKER and recording:
                    recording = False
                    received_bits.clear()

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
            self._transmit(self.outbox._msg, end_idx=len(self.outbox))
        else:
            self._transmit(self.outbox._msg, end_idx=msg_len)

    def start(self) -> None:
        print("Starting Laser loop")

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

