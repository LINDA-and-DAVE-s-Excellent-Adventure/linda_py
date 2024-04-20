from machine import Pin, I2C
from gpio import QWIIC_SCL, QWIIC_SDA
from memory import AmsatI2CBuffer

class LindaI2C:
    def __init__(self, i2c_buffer: AmsatI2CBuffer) -> None:
        self.i2c = I2C(0, scl=Pin(QWIIC_SCL), sda=Pin(QWIIC_SDA), freq=400_000)
        self.i2c.scan()
        
    def __repr__(self) -> str:
        return 'I2C'

    def __str__(self) -> str:
        return 'I2C'
    