import _thread

from encoding import HammingData
from laser import LindaLaser
from iic import LindaI2C
from memory import AmsatI2CBuffer, InboxBuffer, OutboxBuffer

class Linda():
    def __init__(self) -> None:
        print("New LINDA top-level controller")
        # Allocate initial buffers
        inbox = InboxBuffer(64000)
        outbox = OutboxBuffer(64000)
        amsat_buff = AmsatI2CBuffer(32000)
        self.laser = LindaLaser(inbox, outbox)
        # self.i2c = LindaI2C(amsat_buff)

    def _transfer_amsat_buffer_to_outbox(self) -> None:
        """
        Copy data from the I2C buffer from the AMSAT to the Laser outbox
        """
        pass

    def _transfer_inbox_to_amsat_buffer(self) -> None:
        """
        Copy data form the Laser inbox to the AMSAT I2C buffer
        """
        pass

    def start(self):
        # Start the laser listener loop in its own thread
        # _thread.start_new_thread(self.laser.start, ())
        # Start the Amsat i2c listener 
        # _thread.start_new_thread(self.i2c.start, ())
        pass
