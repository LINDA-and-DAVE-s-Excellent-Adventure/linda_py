from micropython import const
from math import log2

# Allows us to try different Hamming message sizes
# SECDED (Single eror correction, double error detection) Hamming encoding will have an extra bit, conveniently fits message in 2^n bits
# Hamming(7,4) -> HAMMING_DATA_SIZE = 4, HAMMING_PARITY_SIZE = 3 -> HAMMING_TOTAL_SIZE = 8
# Hamming(15,11) -> HAMMING_DATA_SIZE = 11, HAMMING_PARITY_SIZE = 4 -> HAMMING_TOTAL_SIZE = 16
# Hamming(31,26) -> HAMMING_DATA_SIZE = 26, HAMMING_PARITY_SIZE = 5 -> HAMMING_TOTAL_SIZE = 32
# etc...
HAMMING_DATA_SIZE = const(4)
HAMMING_PARITY_SIZE = const(3)
HAMMING_TOTAL_SIZE = const(HAMMING_DATA_SIZE + HAMMING_PARITY_SIZE + 1)

class HammingData:
    def __init__(self, encoded_data: bytearray = bytearray(0),  data_string: str = ""):
        self.data_string = data_string
        self.encoded_data = encoded_data
        self.decoded_string = ""
        self.decoded_data = encoded_data

    def __str__(self):
        return f"Data String: {self.data_string} -> Encoded Bits: {self.encoded_data}"
    

    def encode(self, data_string: str) -> int:
        # Save the data string internally
        self.data_string = data_string
        # Encode the data_string and save the resulting bytearray() 
        self.encoded_data = _encode_ascii(data_string)
        return 1

    def decode(self) -> int:
        # Pass a memoryview pointer of the encoded data to the decode_ascii() function
        encoded_mv = memoryview(self.encoded_data)
        decoded = _decode_ascii(encoded_mv)
        print(decoded)
        self.decoded_string = decoded
        return 1
    

def _encode_ascii(data_string):
    """
    Takes a message and encodes representative 8-bit ASCII values throgh GV-configured Hamming encoding.
    Encoded message is stored and returned in an apropriately sized bytearray 

    Args:
        data_string (_str_): String message to encode

    Returns:
        _bytearrary_: Bytearray containing Hamming-encoded original string
    """
    # Encodes the data string to a bytearray with STX and EOT characters at beginning/end
    # Adds STX (0x02 / 0b0000010) ASCII character to front of string
    # Adds EOT (0x04 / 0b0000100) ASCII character to end of string
    data_bytearray = bytearray((chr(0x02)+data_string+chr(0x04)).encode())
    print(data_bytearray)
    # Pad the data bytearray with 0s to make it a multiple of HAMMING_DATA_SIZE bits (ensures proper encoding)
    # remainder = len(bitstream) % HAMMING_DATA_SIZE
    # if remainder != 0:
    #     padding = [0 for _ in range(HAMMING_DATA_SIZE-remainder)]
    #     bitstream.extend(padding)
    hamming_msg_size = int((len(data_bytearray)*HAMMING_TOTAL_SIZE)/HAMMING_DATA_SIZE)
    encoded_bytes = bytearray(hamming_msg_size)
    # Initialize the encoded_bits array to be hamming code size w/ extra bit for double error detection
    encoded_bits = [0] * (HAMMING_DATA_SIZE + HAMMING_PARITY_SIZE + 1)
    # Iterate over HAMMING_DATA_SIZE length chunks of the bitstream to encode
    for chunk_idx in range(0, len(data_bytearray), HAMMING_DATA_SIZE):
        data_chunk = data_bytearray[chunk_idx : chunk_idx+HAMMING_DATA_SIZE]
        print(data_chunk)
        data_idx = 0
        # This is designed so that it will encode any Hamming scheme depending on GVs above
        for i in range(HAMMING_TOTAL_SIZE):
            # This will evaluate to true if i is NOT a power of two (and also not 0)
            if i != 0 and (i & (i-1)) != 0:
                encoded_bits[i] = data_chunk[data_idx]
                data_idx += 1

        # Now calculate parity bits
        for i in range(HAMMING_PARITY_SIZE):
            parity_mask = 0
            # Iterate over bits in Hamming message
            for j in range(HAMMING_TOTAL_SIZE):
                # This will check if each data bit is covered by the i-th parity bit
                # Accomplished by taking bitwise AND between the index in the encoded_bit list and the index of the parity bit
                if j & (2**i):
                    # Toggles parity mask between 1 and 0 depending on parity of encoded bits
                    parity_mask ^= encoded_bits[j]
            # Store this parity bit in a 2^n-th location
            encoded_bits[2**i] = parity_mask & 1
        
        # Finally set 0th bit in encoded_bits to parity of entire message for double error detection
        total_parity = sum(encoded_bits) % 2
        encoded_bits[0] = total_parity      

        print(encoded_bits)  
                        
        # Now cast the list of encoded bits to integer-representation bytes
        encoded_bits_int = int(''.join(str(bit) for bit in encoded_bits), 2)
        # chunk idx iterates as 0,4,8,12... but we want to save each encoded nibble to bytes 0,1,2,3...
        encoded_bytes[int(chunk_idx/HAMMING_DATA_SIZE)] = encoded_bits_int

        print(f"Encoded {data_chunk} into bits: {encoded_bits} -- ASCII {encoded_bits_int} ({chr(encoded_bits_int)})") 

    # For testing
    # print(f"Original bits: {bitstream} (length {len(bitstream)})\nEncoded bits: {all_encoded_bits} (length {len(all_encoded_bits)})")
    return encoded_bytes
 
def _decode_ascii(codeword_mv: memoryview) -> str: 
    """
    Given a bytearray representing an 8-bit ASCII message passed through GV-configued Hamming encoding,
    decode to binary, store bits to list(), and conver to Python _str_

    Args:
        codeword_mv (_memoryview_): Memoryview pointer to the bytearray to decode

    Returns:
        _str_: Decoded message
    """
    # Assume encoding SECDED Hamming encoding, so using whole bytes to encode
    chunk_size = int(HAMMING_TOTAL_SIZE / 8)
    decoded_bits = []
    error_position = 0
    print(f"Decoding: {codeword_mv}")
    for byte_idx in range(0, len(codeword_mv), chunk_size):
        chunk = codeword_mv[byte_idx : byte_idx+chunk_size]
        working_bits = []
        data_bits = []
        # Python will truncate binary, e.g. int(5) = 0b101 instead of 0b00000101
        #   so pad with left-zeros until we get everything in 8-bit chunks
        for byte in chunk:
            bits = f"{byte:08b}"
            working_bits.extend([int(bit) for bit in bits])
        # Now we have the codeword_mv bits in a list, next detect and correct errors
        for i in range(HAMMING_PARITY_SIZE):
            parity_mask = 0
            for j in range(HAMMING_TOTAL_SIZE):
                if j & (2**i):
                    parity_mask ^= working_bits[j]
            error_position += (parity_mask & 1) * (2**i)
        # Error detection and correction
        if error_position >= 1 and error_position <= 7:
            working_bits[error_position - 1] ^= 1
        # Put all the bits in non-2^n indexes into list of decoded bits
        for i, bit in enumerate(working_bits):
            if (i & (i-1)) != 0:
                decoded_bits.append(bit)
                data_bits.append(bit)
        print(f"Chunk: {chunk} -- {working_bits} -- Data: {data_bits}")
    print(f"Decoded bits: {decoded_bits}")
    decoded = binary_list_to_string(decoded_bits)
    print(decoded)
    return decoded

def binary_list_to_string(data_bytearray: list) -> str:
    """
    Takes a list() of integers representing binary values of 8-bit ASCII characters and converts to a string
    E.g. 'f' (ASCII 102) -> [0,1,1,0,0,1,1,0]

    Args:
        data_bytearray (_memoryview_): A memoryview pointer to a list of 1 or 0 integers of an 8-bit ASCII message

    Returns:
        _str_: The 8-bit ASCII string decoded from the binary list
    """
    # Assume we're storing ASCII characters in 8-bit chunks (left-padded 0)
    chunks = [data_bytearray[i:i+8] for i in range(0, len(data_bytearray), 8)]
    print(chunks)
    ascii_string = ""
    for chunk in chunks:
        ascii_code = int(''.join(str(bit) for bit in chunk), 2)
        if ascii_code == 0x02:
            print("Start of sequence")
            continue
        elif ascii_code == 0x04:
            print("End of sequence")
            break
        ascii_string += chr(ascii_code)
        print(f"{ascii_code} -- {chr(ascii_code)}")
    return ascii_string

def hamming_xor(bits_list: memoryview) -> int:
    """
    Takes a list of bits and continuously XOR's across those bits
    Micropython-able reduce(lambda x,y: x^y, )

    Args:
        bits_list (_memoryview_): A memoryview pointer to the list of bits to XOR over

    Returns:
        _int_: The integer position of the bit to flip. If 0, the list is properly encoded/decoded
    """
    # Takes a list of bits, continuously XOR across those bits
    # Can be used to encode or decode a block
    # ENCODING USAGE:
    #   Say you are encoding 4 data bits into a Hamming(7,4) codeword_mv
    #   Place the data bits in the non 2^n indexes (data bits go in index 3, 5, 6, 7)
    #   Set all other parity bit locations (0, 1, 2, 4) to 0
    #   Running that bit list through hamming_xor() will return the index of bit to flip
    #       if not 0, then flip it!
    #       if hamming_xor() returns 0, the bit list represents a valid Hamming codeword_mv
    xor_flag = 0
    for i,bit in enumerate(bits_list):
        if bit:
            xor_flag ^= i
    return xor_flag

pipe = 'When Stubb had departed, Ahab stood for a while leaning over the bulwarks; and then, as had been usual with him of late, calling a sailor of the watch, he sent him below for his ivory stool, and also his pipe. Lighting the pipe at the binnacle lamp and planting the stool on the weather side of the deck, he sat and smoked. \
    In old Norse time, the thrones of the sea-loving Danish kinds were fabricated, saith tradition, of the tusks of the narwhale. How could one look at Ahab then, seated on that tripod of bones, without bethinking him of the royalty it symbolized? For a Khan of the plank, and a king of the sea and a great lord of Leviathans was Ahab. \
    Some moments passed, during which the thick vapor came from his mounth in quick and constant puffs, which blew back again into his face. "How now", he soliloquized at last, withdrawing the tube, "this smoking no longer soothes. Oh, my pipe! hard must it go with me if thy charm be gone! Here have I been unconsciously toiling, not pleasuring- aye, and ignorantly smmoking to the windward all the while; to windward, and with such nervous whiffs, as if, like the dying whale, my final jets were the strongest and the fullest of trouble. What business have I with this pipe? This thing that is meant for sereneness, to send up mild white vapors among mild white hairs, not among torn iron-grey locks like mine. I\'ll smoke no more-"\
    He tossed the still lighted pipe into the sea. The fire hissed in the waves; the same instant the ship shot by the bubble the sinking pipe made. With slouched hat, Ahab lurchingly paced the planks.'