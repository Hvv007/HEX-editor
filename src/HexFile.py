class HexFile:
    def __init__(self, filename: str, columns: int):
        super(__class__, self).__init__()
        self.filename = filename
        self.columns = columns
        self.hex_array = []
        self.hex_array_len = 0
        self.content_array = []
        self.special_characters = ["\a", "\b", "\f", "\n", "\r", "\t", "\v", "\x00"]

    def start(self):
        self.process_content()
        self.format_content()
        self.format_visible_content()

    def decode_hex(self):
        decoded_array = []
        for hex_object in self.hex_array:
            byte_object = bytes.fromhex(hex_object)
            ascii_object = self.decode_byte_to_ascii(byte_object)
            decoded_array.append(ascii_object)
        return decoded_array

    def process_content(self):
        with open(self.filename, "rb") as file_content:
            for line in file_content.readlines():
                for byte in line:
                    self.hex_array_len += 1
                    hex_byte = hex(byte).replace("x", "").upper()
                    if byte >= 16:
                        hex_byte = hex_byte.lstrip("0")
                    self.hex_array.append(hex_byte)

    def format_content(self):
        new_array = []
        for byte in self.hex_array:
            new_array.append(byte)
        self.hex_array = new_array

    def format_visible_content(self):
        new_array = []
        for byte in self.hex_array:
            appendable_byte_to_system = byte
            if self.columns != 16:
                appendable_byte_to_system = int(byte, 16)
                if self.columns == 2:
                    appendable_byte_to_system = format(appendable_byte_to_system, 'b')
                if self.columns == 8:
                    appendable_byte_to_system = format(appendable_byte_to_system, 'o')
                if self.columns == 10:
                    appendable_byte_to_system = str(appendable_byte_to_system)
            new_array.append(appendable_byte_to_system)
        self.content_array = new_array

    def decode_byte_to_ascii(self, byte_object):
        try:
            ascii_object = byte_object.decode("ascii")
        except UnicodeDecodeError:
            ascii_object = "."
        if ascii_object in self.special_characters:
            ascii_object = "."
        return ascii_object
