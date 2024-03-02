from machine import Pin
from utime import sleep_us, sleep_ms, ticks_us, ticks_ms, ticks_diff
from time import sleep

RLED_PIN = 21
GLED_PIN = 19
DETECTOR_PIN = 16
LASER_PIN = 17
SWITCH_PIN = 18
TICK_TIME = 50
PADDING_TIME = 10

TICK_DURATION_MS = 3
TICK_THRESHOLD_MS = 2

led = Pin(RLED_PIN, Pin.OUT)
laser = Pin(LASER_PIN, Pin.OUT)
switch = Pin(SWITCH_PIN, Pin.IN)
detector = Pin(DETECTOR_PIN, Pin.IN)
green = Pin(GLED_PIN, Pin.OUT)

class LindaLaser:
    def __init__(self, buffer_mv) -> None:
        self.buffer = buffer_mv

def flash_led(binary_list):
    for bit in binary_list:
        led.value(bit)
        laser.value(bit)
        sleep_ms(TICK_TIME)

        led.value(0)
        laser.value(0)
        sleep_ms(PADDING_TIME)

def flash_led_bytearray(array):
    for byte in array:
        for bit in bin(byte)[2:]:
            led.value(int(bit))
            laser.value(int(bit))
            sleep_ms(TICK_TIME)

            led.value(0)
            laser.value(0)
            sleep_ms(PADDING_TIME)

def string_to_binary_list(string):
    string_binary = ''.join([f"{ord(letter):08b}" for letter in string])
    bit_list = [int(bit) for bit in string_binary]
    return bit_list

def binary_list_to_string(bit_list):
    # Assume we're storing ASCII characters in 8-bit chunks (left-padded 0)
    chunks = [bit_list[i:i+8] for i in range(0, len(bit_list), 8)]
    print(chunks)
    ascii_string = ""
    for chunk in chunks:
        ascii_code = int(''.join(str(bit) for bit in chunk), 2)
        if ascii_code == 0x02:
            print("Start of sequence")
        elif ascii_code == 0x04:
            print("End of sequence")
            break
        ascii_string += chr(ascii_code)
        print(f"{ascii_code} -- {chr(ascii_code)}")
    return ascii_string

def listen_tick():
    start_time = ticks_ms()
    while ticks_ms() - start_time < TICK_DURATION_MS:
        if not detector.value() == 1:
            led.value(1)
            if ticks_ms() - start_time >= TICK_THRESHOLD_MS:
                print("Laser detected for at least 2ms")
                break
        else:
            led.value(0)
        sleep_ms(1)


test_string = 'hello world'
test_binary = string_to_binary_list(test_string)
while True:
    state = switch.value()
    if state:
        green.value(1)
        laser.value(1)
        listen_tick()
    else:
        green.value(0)
        flash_led(test_binary)
        print("Done")
        sleep(1)
