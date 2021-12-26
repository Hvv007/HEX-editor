import argparse
import curses
import curses.ascii
import os
import sys
from Application import Application, Window


class HexFile:
    def __init__(self, filename: str, columns: int):
        super(__class__, self).__init__()
        self.filename = filename
        self.columns = columns
        self.special_characters = ["\a", "\b", "\f", "\n", "\r", "\t", "\v", "\x00"]
        self.hex_array = []
        self.hex_array_len = 0

    def start(self):
        self.process_content()
        self.format_content()

    def decode_hex(self):
        decoded_array = []
        for line in self.hex_array:
            line_array = []
            for hex_object in line:
                byte_object = bytes.fromhex(hex_object)
                try:
                    ascii_object = byte_object.decode("ascii")
                except UnicodeDecodeError:
                    ascii_object = "."
                if ascii_object in self.special_characters:
                    ascii_object = "."
                line_array.append(ascii_object)
            decoded_array.append(line_array)
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
        i = 0
        line = []
        new_array = []
        for byte in self.hex_array:
            if i == self.columns:
                new_array.append(line)
                line = []
                i = 0
            line.append(byte)
            i += 1
        if line:
            new_array.append(line)
        self.hex_array = new_array


class PyHex(Window):
    def __init__(self, create, read_only, filename, *args, **kwargs):
        super(__class__, self).__init__(*args, **kwargs)
        self.init_colors()
        self.set_cursor_state(0)
        self.columns = 16
        self.last_line = curses.LINES - 2
        self.create = create
        self.readonly = read_only
        self.filename = filename
        self.changed = False
        self.save_dialog = False

        self.max_lines = self.last_line - 3
        self.top_line = self.bottom_line = 0
        self.edit_lines = self.encoded_lines = self.decoded_lines = self.offset_lines = []
        self.cursor_y = self.cursor_x = 0
        self.content_pos_y = self.content_pos_x = 0

        self.up_scroll = -1
        self.down_scroll = 1
        self.left_scroll = -1
        self.right_scroll = 1

        self.edit_keys = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "a", "b", "c", "d", "e", "f"]
        for i, key in enumerate(self.edit_keys):
            self.edit_keys[i] = ord(str(key))

        self.edited_position = 0  # Начальная позиция в байте при изменении: 0 - левая, 1 - правая

        self.title = "HEX-editor"
        self.title_x = int
        self.title_y = 0
        self.offset_title = "Offset (h)"
        self.offset_title_x = 2
        self.offset_title_y = 1
        self.offset_len = 8
        self.offset_text = []
        self.offset_text_x = 2
        self.offset_text_y = 2
        self.encoded_title = ""
        self.encoded_title_x = 13
        self.encoded_title_y = 1
        self.encoded_text_x = 13
        self.encoded_text_y = 2
        self.decoded_title = "Decoded text"
        self.decoded_title_x = int
        self.decoded_title_y = 1
        self.decoded_text = []
        self.decoded_text_x = int
        self.decoded_text_y = 2

        if self.create:
            file = open(self.filename, "w")
            file.close()
        self.file = HexFile(self.filename, self.columns)
        self.file.start()

        self._status_bar_text = "{}".format(os.path.basename(self.filename))
        self.status_bar_text = ""
        self.status_bar_color = 3
        self.get_status_bar_text = lambda: self._status_bar_text + self.status_bar_text

        self.edited_array = []
        for line in self.file.hex_array:
            edited_line = ["--"] * len(line)
            self.edited_array.append(edited_line)

        self.decoded_text = self.file.decode_hex()
        self.bottom_line = len(self.file.hex_array)

    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_WHITE)

    def check_keys(self):
        if self.save_dialog:
            if self.key_pressed == ord("y"):
                self.save()
            if self.key_pressed == ord("n"):
                self.changed = self.save_dialog = False
                self.exit()
            return

        if self.key_pressed == curses.ascii.ESC or self.key_pressed == ord("q"):
            self.exit()

        if self.key_pressed == curses.KEY_UP:
            self.scroll_vertically(self.up_scroll)
        elif self.key_pressed == curses.KEY_DOWN:
            self.scroll_vertically(self.down_scroll)
        if self.key_pressed == curses.KEY_LEFT:
            self.scroll_horizontally(self.left_scroll)
        elif self.key_pressed == curses.KEY_RIGHT:
            self.scroll_horizontally(self.right_scroll)

        if self.key_pressed in self.edit_keys and not self.readonly:
            char = chr(self.key_pressed)
            self.edit(char, self.content_pos_y, self.content_pos_x)
        if self.key_pressed == curses.ascii.BS and not self.readonly:
            self.clear_edit(self.content_pos_y, self.content_pos_x)

    def exit(self):
        if self.changed:
            self.save_dialog = True
            return

        curses.endwin()
        sys.exit()

    def update(self):
        self.title_x = int((self.width // 2) - (len(self.title) // 2) - len(self.title) % 2)
        self.encoded_title = ""
        for i in range(0, self.columns):
            hex_ch = hex(i).replace("x", "").upper()
            if i >= 16:
                hex_ch = hex_ch.lstrip("0")
            self.encoded_title += hex_ch + " "

        self.decoded_title_x = self.encoded_title_x + len(self.encoded_title) + 2
        self.decoded_text_x = self.decoded_title_x

        total_lines = len(self.file.hex_array)
        self.offset_text = []
        for i in range(0, total_lines):
            offset = hex(i * self.columns).replace("x", "").upper()
            offset = "0" * (self.offset_len - len(str(offset))) + str(offset)
            self.offset_text.append(offset)

        self.encoded_lines = self.file.hex_array[self.top_line:self.top_line + self.max_lines]
        self.decoded_lines = self.decoded_text[self.top_line:self.top_line + self.max_lines]
        self.edit_lines = self.edited_array[self.top_line:self.top_line + self.max_lines]
        self.offset_lines = self.offset_text[self.top_line:self.top_line + self.max_lines]

        if self.changed:
            self.status_bar_text = "* "
        else:
            self.status_bar_text = ""

        if self.save_dialog:
            self.status_bar_text = " | Would you like to save your file? Y for yes, N for no"

    def late_update(self):
        self.draw_ornament()
        self.draw_titles()
        self.draw_offset()
        self.draw_encoded()
        self.draw_decoded()
        self.draw_status_bar()

    def draw_ornament(self):
        self.draw_text(self.offset_text_y, self.offset_text_x - 1,
                       "┌" + "─" * (self.offset_len + (self.columns * 4 + 5)) + "┐", 1)
        self.draw_text(self.offset_text_y, self.encoded_text_x - 2, "┬", 1)
        self.draw_text(self.offset_text_y, self.decoded_text_x - 2, "┬", 1)

        self.draw_text(self.last_line, self.offset_text_x - 1,
                       "└" + "─" * (self.offset_len + (self.columns * 4 + 5)) + "┘", 1)
        self.draw_text(self.last_line, self.decoded_text_x - 2, "┴", 1)
        self.draw_text(self.last_line, self.encoded_text_x - 2, "┴", 1)

        for i in range(self.offset_text_y + 1, self.last_line):
            self.draw_text(i, self.offset_text_x - 1, "│" + " " * (self.offset_len + 1) +
                           "│" + " " * (self.columns * 3 + 1) + "│" + " " * (self.columns + 1) + "│", 1)

    def draw_titles(self):
        self.draw_text(self.title_y, self.title_x, self.title, 2)
        self.draw_text(self.offset_title_y, self.offset_title_x, self.offset_title, 1)
        self.draw_text(self.encoded_title_y, self.encoded_title_x, self.encoded_title, 1)
        self.draw_text(self.decoded_title_y, self.decoded_title_x, self.decoded_title, 1)

    def draw_offset(self):
        y_coord = self.offset_text_y + 1
        x_coord = self.offset_text_x
        for offset in self.offset_lines:
            self.draw_text(y_coord, x_coord, offset, 1)
            y_coord += 1

    def draw_encoded(self):
        x_coord = self.encoded_text_x
        y_coord = self.encoded_text_y + 1
        x_offset = 0
        for y, line in enumerate(self.encoded_lines):
            for x, byte in enumerate(line):
                edited_color = 4
                normal_color = 1
                if y == self.cursor_y and x == self.cursor_x:
                    edited_color = 5
                    normal_color = 3

                if (self.edit_lines[y][x][0] != "-") and (self.edit_lines[y][x][1] != "-"):
                    self.draw_text(y_coord, x_coord + x_offset, self.edit_lines[y][x], edited_color)
                elif self.edit_lines[y][x][1] != "-":
                    self.draw_text(y_coord, x_coord + x_offset, self.edit_lines[y][x][1] + byte[0], edited_color)
                elif self.edit_lines[y][x][0] != "-":
                    self.draw_text(y_coord, x_coord + x_offset, self.edit_lines[y][x][0] + byte[1], edited_color)
                elif self.edit_lines[y][x] == "--":
                    self.draw_text(y_coord, x_coord + x_offset, byte, normal_color)
                x_offset += 3
            x_offset = 0
            y_coord += 1

    def draw_decoded(self):
        x_coord = self.decoded_text_x
        y_coord = self.decoded_text_y + 1
        for y, line in enumerate(self.decoded_lines):
            x_offset = 0
            for x, char in enumerate(line):
                edited_color = 4
                normal_color = 1
                edited = False

                if y == self.cursor_y and x == self.cursor_x:
                    edited_color = 5
                    normal_color = 3

                if self.edit_lines[y][x] == "--":
                    self.draw_text(y_coord, x_coord + x_offset, char, normal_color)
                elif self.edit_lines[y][x][0] == "-":
                    hex_object = self.encoded_lines[y][x][0] + self.edit_lines[y][x][1]
                    edited = True
                elif self.edit_lines[y][x][1] == "-":
                    hex_object = self.edit_lines[y][x][0] + self.encoded_lines[y][x][1]
                    edited = True
                else:
                    hex_object = self.edit_lines[y][x]
                    edited = True

                if edited:
                    byte_object = bytes.fromhex(hex_object)
                    try:
                        ascii_object = byte_object.decode("ascii")
                    except UnicodeDecodeError:
                        ascii_object = "."
                    if ascii_object in self.file.special_characters:
                        ascii_object = "."
                    self.draw_text(y_coord, x_coord + x_offset, ascii_object, edited_color)
                x_offset += 1
            y_coord += 1

    def draw_status_bar(self):
        self.draw_text(self.last_line + 1, 0, " "*(self.width-1), self.status_bar_color)
        self.draw_text(self.last_line + 1, 0, self.get_status_bar_text(), self.status_bar_color)

    def scroll_horizontally(self, direction):
        next_position = self.cursor_x + direction
        if direction in (self.left_scroll, self.right_scroll):
            self.edited_position = 0

        if direction == self.left_scroll:
            if (self.cursor_x >= 0) and (next_position >= 0):
                self.cursor_x = next_position
                self.content_pos_x += direction
                return
            if next_position < 0 < self.content_pos_y:
                self.cursor_x = self.columns - 1
                self.content_pos_x = self.columns - 1
                self.scroll_vertically(self.up_scroll)
                return
        if direction == self.right_scroll:
            if next_position < self.columns:
                self.cursor_x = next_position
                self.content_pos_x += direction
                return
            if next_position == self.columns:
                self.cursor_x = 0
                self.content_pos_x = 0
                self.scroll_vertically(self.down_scroll)
                return

    def scroll_vertically(self, direction):
        next_line = self.cursor_y + direction
        if direction == self.up_scroll:
            if self.top_line > 0 and self.cursor_y == 0:
                self.top_line += direction
                self.content_pos_y += direction
                return
            if self.top_line > 0 or self.cursor_y > 0:
                self.cursor_y = next_line
                self.content_pos_y += direction
                return
        if direction == self.down_scroll:
            if (next_line == self.max_lines) and (self.top_line + self.max_lines < self.bottom_line):
                self.top_line += direction
                self.content_pos_y += direction
                return
            if (next_line < self.max_lines) and (self.top_line + next_line < self.bottom_line):
                self.cursor_y = next_line
                self.content_pos_y += direction
                return

    def edit(self, char, cursor_y, cursor_x):
        if char.isalpha():
            char = char.upper()
        if cursor_x < len(self.edited_array[cursor_y]):
            if self.edited_position == 0:
                self.edited_array[cursor_y][cursor_x] = str(char) + self.edited_array[cursor_y][cursor_x][1]
                self.edited_position = 1
                self.changed = True
                return

            if self.edited_position == 1:
                self.edited_array[cursor_y][cursor_x] = self.edited_array[cursor_y][cursor_x][0] + str(char)
                self.edited_position = 0
                self.changed = True
                self.scroll_horizontally(self.right_scroll)
                return

    def clear_edit(self, cursor_y, cursor_x):
        no_edit = True
        for y, line in enumerate(self.edited_array):
            for x, byte in enumerate(line):
                if y == cursor_y and x == cursor_x:
                    self.edited_array[y][x] = "--"
                    self.scroll_horizontally(self.left_scroll)
                    self.edited_position = 0
                if byte != "--":
                    no_edit = False
        if no_edit:
            self.changed = False

    def save(self):
        file_content = b''
        for y, line in enumerate(self.file.hex_array):
            for x, byte in enumerate(line):
                edited_byte = self.edited_array[y][x]
                if edited_byte == "--":
                    hex_byte = byte
                elif edited_byte[0] == "-":
                    hex_byte = byte[0] + edited_byte[1]
                elif edited_byte[1] == "-":
                    hex_byte = edited_byte[0] + byte[1]
                else:
                    hex_byte = edited_byte
                file_content += bytes.fromhex(hex_byte)
        with open(self.filename, "wb") as f:
            f.write(file_content)
            f.close()
        self.changed = False
        self.save_dialog = False
        self.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HEX-editor', add_help=False,
                                     usage='main.py [OPTIONS] FILE_NAME')
    parser.add_argument("-h", "--help", help="показывает это сообщение", action="help")
    parser.add_argument("-c", "--create", help="флаг для создания нового файла", action="store_true")
    parser.add_argument("-r", "--read_only", help="флаг только для чтения", action="store_true")
    parser.add_argument("FILE_NAME", help="название файла")
    args = parser.parse_args()
    create = args.create
    read_only = args.read_only
    filename = args.FILE_NAME
    app: Application = Application()
    app.set_main_window(PyHex(create, read_only, filename, app.stdscr, app))
    app.run()
