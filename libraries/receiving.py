from machine import Pin
from micropython import const
import utime

TICK_DURATION_MS = 10
LASER_THRESHOLD_MS = 7
DETECTOR_PIN = 16
SWITCH_PIN = 18
LED_PIN = 21
START_MARKER = const(0xBEEF)
END_MARKER = const(0xDEAD)

detector = Pin(DETECTOR_PIN, Pin.IN)
switch = Pin(SWITCH_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)
received_bits = []
recording = False

message = "hello world"

def decode_message(received_bits):
    print(received_bits)

def process_tick():
    global received_bits, recording, last_read_time
    laser_state = detector.value()  # Read current detector state
    bit_value = 1 if utime.ticks_ms() - last_read_time >= LASER_THRESHOLD_MS else 0
    last_read_time = utime.ticks_ms()
    print(f"Read bit: {bit_value}")

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

def transmit_bit(bit):
    led.value(bit)
    utime.sleep_ms(LASER_THRESHOLD_MS)
    led.value(0)

def transmit_message():
    # Transmit START_MARKER
    for bit in f"{START_MARKER:b}": 
        transmit_bit(int(bit))

    # Transmit message (encoded as binary)
    for char in message:
        for bit in f"{ord(char):b}": 
            transmit_bit(int(bit))

    # Transmit END_MARKER
    for bit in f"{END_MARKER:b}":
        transmit_bit(int(bit))

    utime.sleep(2)  # Wait 2 seconds


def main_loop():
    global last_read_time
    last_read_time = utime.ticks_ms()

    while True:
        if not switch.value():
            transmit_message()
        else:
            utime.sleep_ms(TICK_DURATION_MS)
            process_tick()
            print("done with tick")
