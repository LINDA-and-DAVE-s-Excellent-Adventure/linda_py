# Header sizes in bytes
import gc
from sys import stdout

OUTBOX_HEADER_SIZE = 3
INBOX_HEADER_SIZE = 7


class MemoryBuffer:
    def __init__(self, size_bytes) -> None:
        # Initialize the memory off of the heap
        data = bytearray(size_bytes)
        # Create a memoryview to it, so we can sub-view the memory in the derived classes
        self._data = memoryview(data)

    def __str__(self) -> str:
        return "Memory buffer"

    def __repr__(self) -> str:
        return "Memory buffer"
    
    def _memoryview_int(self, mem: memoryview) -> int:
        """
        Given a memoryview, cast its entirety to a big-endiant int and return


        Args:
            mem (memoryview): The memoryview to cast to an int. Typically a self variable

        Returns:
            int: Integer representation of the total contents of the given memoryview
        """
        return int.from_bytes(mem, 'big')
    
class AmsatI2CBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes)

class OutboxBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes+OUTBOX_HEADER_SIZE)
        # Byte 0 of _data flags whether _msg is ready to send
        self.msg_ready = memoryview(self._data[:1])
        # Byte 1-2 of _data stores length of message (in bytes)
        self._msg_len = memoryview(self._data[1:3])
        # Bytes 3-n of _data store the outgoing message
        self._msg = memoryview(self._data[3:])

    def __str__(self) -> str:
        return self._print_outbox_ascii()
    
    def __repr__(self) -> str:
        return f"OutboxBuffer: {len(self._msg)} bytes ({len(self._data)} bytes total)\n\
                    Message length = {self._memoryview_int(self._msg_len)}\n\
                    Msg_ready = {bool(self.msg_ready[0])}"
    
    def __bool__(self) -> bool:
        return bool(self.msg_ready[0])
    
    def __len__(self) -> int:
        # Return the length of the message
        return self._memoryview_int(self._msg_len)

    def _read_ascii(self, _msg: str) -> None:
        """
        Write an ASCII string to the outbox. Updates 

        Args:
            _msg (str): ASCII string to save to outbox message buffer
'        """
        if len(_msg) > len(self._msg):
            print(f"Your message ({len(_msg)} bytes) is larger than the message buffer ({len(self._msg)} bytes)\n"\
                  "The message will be truncated.")
        # Set the message length
        length_bytes = len(_msg).to_bytes(2, 'big')
        for i,byte in enumerate(length_bytes):
            self._msg_len[i] = byte
        for i, char in enumerate(_msg):
            if i+1 >= len(self._msg):
                break
            self._msg[i] = ord(char)
        gc.collect()

    def _print_outbox_ascii(self, chunk_size: int=64, print_len: int=-1) -> str:
        """
        Print the contents of the outbox message. Iterates over given chunk size, decodes, and prints to limit 
            memory usage during printing

        Args:
            chunk_size (int, optional): The size of chunks to decode and print. Defaults to 64.
            print_len (int, optional): The length of the outbox to print If -1, prints whole message. Defaults to -1.

        Returns:
            str: Empty string to signal end of ASCII text and provide newline
        """
        start = 0
        decoded_chunk = ''
        gc.collect()
        while start < len(self._msg):
            chunk = self._msg[start: start+chunk_size]
            decoded_chunk = bytes(chunk).decode('ascii')
            stdout.write(decoded_chunk)
            start += chunk_size
        gc.collect()
        return ''

    def _set_msg_ready(self, ready:bool=True) -> None:
        """
        Sets the messsage ready flag in the outbox header

        Args:
            ready (bool, optional): Whether the outbox _msg is ready to send. Defaults to True.
        """
        if ready:
            self.msg_ready[0] = 1
        else:
            self.msg_ready[0] = 0

class InboxBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes+INBOX_HEADER_SIZE)
        # Byte 0 of _data flags whether incoming data is loitering or recording
        self._recording_flag = memoryview(self._data[:1])
        # Bytes 1-2 of _data stores the message length as a 16-bit integer
        self._msg_len = memoryview(self._data[1:3])
        # Bytes 3-4 of _data is the _loiter buffer
        self._loiter = memoryview(self._data[3:5])
        self._loiter_idx = 0
        # Bytes 5-n of _data store the incoming message
        self._msg = memoryview(self._data[5:])
        self._msg_idx = 0
        # Externally available representations of 
        self.recording = bool(self._recording_flag[0])
        self.loiter = hex(self._memoryview_int(self._loiter))

    def __str__(self) -> str:
        return super().__str__()
    
    def __repr__(self) -> str:
        return super().__repr__()
    
    def set_recording(self, recording:bool=True) -> None:
        """
        Set the recording flag in the inbox header

        Args:
            recording (bool, optional): Whether to record incoming data. Defaults to True.
        """
        if recording:
            self._recording_flag[0] = 1
        else:
            self._recording_flag[0] = 0
        self.recording = bool(self._recording_flag[0])

    def _loiter_value(self) -> int:
        """
        Return the current integer value of the _loiter buffer

        Returns:
            int: Integer representation of the _loiter buffer
        """
        return int.from_bytes(self._loiter[:], 'big')
    
    def _loiter_byte(self, byte_int: int) -> None:
        """
        Takes a byte and stores it in the _loiter buffer. Updates _loiter_idx to next idx to write into,
            and wraps around automatically after writing 4th byte

        Args:
            int (int): Byte to place into the loiter buffer
        """
        self._loiter[self._loiter_idx] = byte_int
        self._loiter_idx = (self._loiter_idx + 1) % 2

        self.loiter = hex(self._memoryview_int(self._loiter))
        print(self.loiter)
        return None
    
    def rx_byte(self, byte_int: int) -> None:
        if self.recording:
            self._msg[self._msg_idx] = byte_int
            self._msg_idx += 1
        else:
            self._loiter_byte(byte_int)
            if self.loiter == 0xbeef:
                self.set_recording()


# to = InboxBuffer(100)
# import random
# from utime import sleep_us
# rx_bits = []
# while True:
#     bit = random.randint(0,1)
#     print(f"Random bit: {bit}")
#     if len(rx_bits) < 7:
#         rx_bits.append(bit)
#     else:
#         rx_byte = int("".join(str(bit) for bit in rx_bits), 2)
#         print(f"Recieved 8 bits! Processing byte: {rx_byte} ({chr(rx_byte)})")
#         to.rx_byte(rx_byte)
#         rx_bits.clear()
#     sleep_us(250000)

    