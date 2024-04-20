# Header sizes in bytes
import gc
from sys import stdout

class MemoryBuffer:
    def __init__(self, size_bytes) -> None:
        # Initialize the memory off of the heap
        data = bytearray(size_bytes)
        # Create a memoryview to it, so we can sub-view the memory in the derived classes
        self._data = memoryview(data)
        self._data_len = 0

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
        if self._data_len == 0:
            print("This MemoryBuffer is empty!")
        else:
            if print_len == -1:
                print_len = self._data_len
            while start < print_len:
                chunk = self._data[start: start+chunk_size]
                decoded_chunk = bytes(chunk).decode(encoding)
                stdout.write(decoded_chunk)
                start += chunk_size
        gc.disable()
        return ''
    
    def _read_ascii(self, _msg: str) -> None:
        """
        Write an ASCII string to the memory buffer. 

        Args:
            _msg (str): ASCII string to save to outbox message buffer
'        """
        gc.collect()
        if len(_msg) > len(self._data):
            print(f"Your message ({len(_msg)} bytes) is larger than the message buffer ({len(self._data)} bytes)\n"\
                  "The message will be truncated.")
        # Set the message length
        self._data_len = len(_msg)
        for i, char in enumerate(_msg):
            if i+1 >= len(self._data):
                break
            self._data[i] = ord(char)
        gc.collect()
        
class AmsatI2CBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes)

class OutboxBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes)
        self.msg_ready = False
        # Bytes 3-n of _data store the outgoing message
        self._msg = memoryview(self._data[3:])

    def __str__(self) -> str:
        return self._print_data_ascii()
    
    def __repr__(self) -> str:
        return f"OutboxBuffer: {len(self._msg)} bytes ({len(self._data)} bytes total)\n\
                    Message length = {self._data_len}\n\
                    Msg_ready = {self.msg_ready}"
    
    def __bool__(self) -> bool:
        return self.msg_ready
    
    def __len__(self) -> int:
        # Return the length of the message
        return self._data_len

    def _set_msg_ready(self, ready:bool=True) -> None:
        """
        Sets the messsage ready flag

        Args:
            ready (bool, optional): Whether the outbox _msg is ready to send. Defaults to True.
        """
        if ready:
            self.msg_ready = True
        else:
            self.msg_ready = False

class InboxBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes)
        self.recording = False

    def __str__(self) -> str:
        return self._print_data_ascii()
    
    def __repr__(self) -> str:
        return super().__repr__()
    
    def __len__(self) -> int:
        return self._data_len
    
    def set_recording(self, recording:bool=True) -> None:
        """
        Set the recording flag

        Args:
            recording (bool, optional): Whether to record incoming data. Defaults to True.
        """
        if recording:
            self.recording = 1
        else:
            self.recording = 0
        self.recording = bool(self.recording)