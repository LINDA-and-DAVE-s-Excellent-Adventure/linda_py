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
    
    def _print_data_ascii(self, chunk_size: int=64, print_len: int=-1, encoding: str='ascii') -> str:
        """
        Print the contents of the memoryview. Iterates over given chunk size, decodes, and prints to limit 
            memory usage during printing

        Args:
            chunk_size (int, optional): The size of chunks to decode and print. Defaults to 64.
            print_len (int, optional): The length of the outbox to print If -1, prints whole message. Defaults to -1.

        Returns:
            str: Empty string to signal end of ASCII text and provide newline
        """
        gc.enable()
        start = 0
        decoded_chunk = ''
        if print_len == -1:
            print_len = len(self._data)
        while start < print_len:
            chunk = self._data[start: start+chunk_size]
            decoded_chunk = bytes(chunk).decode(encoding)
            stdout.write(decoded_chunk)
            start += chunk_size
        gc.disable()
        return ''
        
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
        return self._print_data_ascii()
    
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
        gc.collect()
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
        self.msg_len = 0
        self.msg_idx = 0
        self.recording = False

    def __str__(self) -> str:
        return self._print_data_ascii(self.msg_len)
    
    def __repr__(self) -> str:
        return super().__repr__()
    
    def set_recording(self, recording:bool=True) -> None:
        """
        Set the recording flag in the inbox header

        Args:
            recording (bool, optional): Whether to record incoming data. Defaults to True.
        """
        if recording:
            self.recording = 1
        else:
            self.recording = 0
        self.recording = bool(self.recording)
    
    def rx_byte(self, byte_int: int) -> None:
        if self.recording:
            self._data[self.msg_idx] = byte_int
            self.msg_idx += 1
    