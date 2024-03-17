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

class OutboxBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes+OUTBOX_HEADER_SIZE)
        # Byte 0 of _data flags whether msg is ready to send
        self.msg_ready = memoryview(self._data[:1])
        # Byte 1-2 of _data stores length of message
        self.msg_len = memoryview(self._data[1:3])
        # Bytes 3-n of _data store the outgoing message
        self.msg = memoryview(self._data[3:])

    def __str__(self) -> str:
        return self._print_outbox_ascii()
    
    def __repr__(self) -> str:
        return self._print_outbox_ascii()
    
    def __len__(self) -> int: 
        return int.from_bytes(self.msg_len, 'big')
    
    def _read_ascii(self, msg: str) -> None:
        """
        Write an ASCII string to the outbox. Updates 

        Args:
            msg (str): ASCII string to save to outbox message buffer
'        """
        if len(msg) > len(self.msg):
            print(f"Your message ({len(msg)} bytes) is larger than the message buffer ({len(self.msg)} bytes)\n"\
                  "The message will be truncated.")
        # Set the message length
        length_bytes = len(msg).to_bytes(2, 'big')
        for i,byte in enumerate(length_bytes):
            self.msg_len[i] = byte
        for i, char in enumerate(msg):
            if i+1 >= len(self.msg):
                break
            self.msg[i] = ord(char)

    def _print_outbox_ascii(self, chunk_size: int=256) -> str:
        start = 0
        decoded_chunk = ''
        gc.collect()
        while start < len(self.msg):
            chunk = self.msg[start: start+chunk_size]
            decoded_chunk = bytes(chunk).decode('ascii')
            stdout.write(decoded_chunk)
            start += chunk_size
        gc.collect()
        return ''

    def _set_msg_ready(self, ready:bool=True) -> None:
        """
        Sets the messsage ready flag in the outbox header

        Args:
            ready (bool, optional): Whether the outbox msg is ready to send. Defaults to True.
        """
        if ready:
            self.msg_ready[0] = 1
        else:
            self.msg_ready[0] = 0

    

class InboxBuffer(MemoryBuffer):
    def __init__(self, size_bytes) -> None:
        super().__init__(size_bytes+INBOX_HEADER_SIZE)
        # Byte 0 of _data flags whether incoming data is loitering or recording
        self.recording = memoryview(self._data[:1])
        # Bytes 1-2 of _data stores the message length
        self.msg_len = memoryview(self._data[1:3])
        # Bytes 3-7 of _data is the loiter buffer
        self.loiter = memoryview(self._data[3:8])
        # Bytes 8-n of _data store the incoming message
        self.msg = memoryview(self._data[8:])

    def __str__(self) -> str:
        return super().__str__()
    
    def __repr__(self) -> str:
        return super().__repr__()
    
    def _set_recording(self, recording:bool=True) -> None:
        """
        Set the recording flag in the inbox header

        Args:
            recording (bool, optional): Whether to record incoming data. Defaults to True.
        """
        if recording:
            self.recording[0] = 1
        else:
            self.recording[0] = 0
    
