import curses
import curses.ascii
import os
import sys
from src.Application import Window
from src.HexFile import HexFile


class PyHex(Window):
    def __init__(self, create, read_only, filename, columns, *args, **kwargs):
        super(__class__, self).__init__(*args, **kwargs)
        self.init_colors()
        self.set_cursor_state(0)
        self.columns = columns
        self.last_line = curses.LINES - 2
        self.create = create
        self.insert_delete_mode = False
        self.readonly = read_only
        self.filename = filename
        self.changed = False
        self.save_dialog = False

        self.max_lines = self.last_line - 3
        self.top_line = self.bottom_line = 0
        self.edit_lines = self.encoded_lines = self.decoded_lines = self.offset_lines = []
        self.cursor_y = self.cursor_x = 0

        self.up_scroll = -1
        self.down_scroll = 1
        self.left_scroll = -1
        self.right_scroll = 1

        self.edit_keys = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "a", "b", "c", "d", "e", "f"]
        for i, key in enumerate(self.edit_keys[:self.columns]):
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
        self.decoded_text_x = int
        self.decoded_text_y = 2
        self.decoded_text = []

        if self.create:
            file = open(self.filename, "w")
            file.close()
        self.file = HexFile(self.filename, self.columns)
        self.file.start()
        self._status_bar_text = "{}".format(os.path.basename(self.filename))
        self.status_bar_text = ""
        self.status_bar_color = 3
        self.get_status_bar_text = lambda: self._status_bar_text + self.status_bar_text

        self.edited_array = ["--"] * len(self.file.content_array)
        self.decoded_text = self.file.decode_hex()
        self.bottom_line = len(self.file.content_array) // self.columns
        self.undo_stack = []
        self.redo_stack = []

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

        if self.key_pressed == ord("i"):
            self.insert_delete_mode = not self.insert_delete_mode

        if self.key_pressed == curses.KEY_UP:
            self.scroll_vertically(self.up_scroll)
        elif self.key_pressed == curses.KEY_DOWN:
            self.scroll_vertically(self.down_scroll)
        if self.key_pressed == curses.KEY_LEFT:
            self.scroll_horizontally(self.left_scroll)
        elif self.key_pressed == curses.KEY_RIGHT:
            self.scroll_horizontally(self.right_scroll)

        if self.key_pressed in self.edit_keys and not self.readonly:
            if self.cursor_y * self.columns + self.cursor_x >= len(self.file.content_array) \
                    and self.file.content_array:
                return
            char = chr(self.key_pressed)
            if char.isalpha():
                char = char.upper()
            if self.insert_delete_mode:
                self.undo_stack.append(["insert", self.cursor_y, self.cursor_x, char + '0'])
                self.insert(self.cursor_y, self.cursor_x, char + '0')
            else:
                self.edit(char)
        if self.key_pressed == curses.ascii.BS and not self.readonly:
            if self.cursor_y * self.columns + self.cursor_x >= len(self.file.content_array):
                return
            if self.insert_delete_mode:
                self.undo_stack.append(["delete", self.cursor_y, self.cursor_x,
                                        self.file.content_array[self.cursor_y * self.columns + self.cursor_x]])
                self.delete(self.cursor_y, self.cursor_x)
            else:
                self.clear_edit()
        if self.key_pressed == 26:  # Ctrl + Z
            self.undo()
        if self.key_pressed == 24:  # Ctrl + X
            self.redo()

    def undo(self):
        if self.undo_stack:
            action_type, y, x, char = self.undo_stack.pop()
            if action_type == "edit":
                self.redo_stack.append(['edit', y, x, self.edited_array[y * self.columns + x]])
                self.edited_array[y * self.columns + x] = char
            if action_type == "insert":
                self.redo_stack.append(['delete', y, x, char])
                self.delete(y, x)
            if action_type == "delete":
                self.redo_stack.append(['insert', y, x, char])
                self.insert(y, x, char)
            if not self.undo_stack:
                self.changed = False

    def redo(self):
        if self.redo_stack:
            action_type, y, x, char = self.redo_stack.pop()
            if action_type == "edit":
                self.undo_stack.append(['edit', y, x, self.edited_array[y * self.columns + x]])
                self.edited_array[y * self.columns + x] = char
            if action_type == "insert":
                self.undo_stack.append(['delete', y, x, char])
                self.delete(y, x)
            if action_type == "delete":
                self.undo_stack.append(['insert', y, x, char])
                self.insert(y, x, char)
            self.changed = True

    def insert(self, y, x, char):
        self.file.content_array.insert(y * self.columns + x, char)
        self.edited_array.insert(y * self.columns + x, char)
        self.decoded_text.insert(y * self.columns + x, self.file.decode_byte_to_ascii(str.encode(char)))
        self.bottom_line = len(self.file.content_array) // self.columns
        self.changed = True
        pass

    def delete(self, y, x):
        self.file.content_array.pop(y * self.columns + x)
        self.edited_array.pop(y * self.columns + x)
        self.decoded_text.pop(y * self.columns + x)
        self.bottom_line = len(self.file.content_array) // self.columns
        self.changed = True
        pass

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

        total_lines = len(self.file.content_array) // self.columns + 1
        self.offset_text = []
        for i in range(0, total_lines):
            offset = hex(i * self.columns).replace("x", "").upper()
            offset = "0" * (self.offset_len - len(str(offset))) + str(offset)
            self.offset_text.append(offset)

        self.encoded_lines = \
            self.file.content_array[self.top_line * self.columns:(self.top_line + self.max_lines) * self.columns]
        self.decoded_lines = \
            self.decoded_text[self.top_line * self.columns:
                              (self.top_line + self.max_lines) * self.columns]
        self.edit_lines = \
            self.edited_array[self.top_line * self.columns:(self.top_line + self.max_lines) * self.columns]
        self.offset_lines = \
            self.offset_text[self.top_line:self.top_line + self.max_lines]

        if self.changed:
            self.status_bar_text = "*"
        else:
            self.status_bar_text = ""
        if self.insert_delete_mode:
            self.status_bar_text += " insert/delete mode"
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
        for i, byte in enumerate(self.encoded_lines):
            x = i % self.columns
            y = i // self.columns
            x_offset = x * 3
            y_offset = y
            edited_color = 4
            normal_color = 1
            if y == self.cursor_y - self.top_line and x == self.cursor_x:
                edited_color = 5
                normal_color = 3

            if (self.edit_lines[i][0] != "-") and (self.edit_lines[i][1] != "-"):
                self.draw_text(y_coord + y_offset, x_coord + x_offset, self.edit_lines[i], edited_color)
            elif self.edit_lines[i][1] != "-":
                self.draw_text(y_coord + y_offset, x_coord + x_offset, self.edit_lines[i][1] + byte[0], edited_color)
            elif self.edit_lines[i][0] != "-":
                self.draw_text(y_coord + y_offset, x_coord + x_offset, self.edit_lines[i][0] + byte[1], edited_color)
            elif self.edit_lines[i] == "--":
                self.draw_text(y_coord + y_offset, x_coord + x_offset, byte, normal_color)

    def draw_decoded(self):
        x_coord = self.decoded_text_x
        y_coord = self.decoded_text_y + 1
        for i, char in enumerate(self.decoded_lines):
            x = i % self.columns
            y = i // self.columns
            edited_color = 4
            normal_color = 1
            edited = False

            if y == self.cursor_y - self.top_line and x == self.cursor_x:
                edited_color = 5
                normal_color = 3
            if self.edit_lines[i] == "--":
                self.draw_text(y_coord + y, x_coord + x, char, normal_color)
            elif self.edit_lines[i][0] == "-":
                hex_object = self.encoded_lines[i][0] + self.edit_lines[i][1]
                edited = True
            elif self.edit_lines[i][1] == "-":
                hex_object = self.edit_lines[i][0] + self.encoded_lines[i][1]
                edited = True
            else:
                hex_object = self.edit_lines[i]
                edited = True

            if edited:
                byte_object = bytes.fromhex(hex_object)
                try:
                    ascii_object = byte_object.decode("ascii")
                except UnicodeDecodeError:
                    ascii_object = "."
                if ascii_object in self.file.special_characters:
                    ascii_object = "."
                self.draw_text(y_coord + y, x_coord + x, ascii_object, edited_color)

    def draw_status_bar(self):
        self.draw_text(self.last_line + 1, 0, " "*(self.width-1), self.status_bar_color)
        self.draw_text(self.last_line + 1, 0, self.get_status_bar_text(), self.status_bar_color)

    def scroll_horizontally(self, direction):
        if direction in (self.left_scroll, self.right_scroll):
            self.edited_position = 0
        if direction == self.left_scroll:
            if self.cursor_x == 0:
                if self.cursor_y == 0:
                    return
                self.cursor_x = self.columns - 1
                self.scroll_vertically(self.up_scroll)
                return
            self.cursor_x += direction
            return
        if direction == self.right_scroll:
            if self.cursor_x == self.columns - 1:
                self.cursor_x = 0
                self.scroll_vertically(self.down_scroll)
                return
            self.cursor_x += direction
            return

    def scroll_vertically(self, direction):
        if direction == self.up_scroll:
            if self.cursor_y == 0:
                return
            if self.cursor_y == self.top_line:
                self.cursor_y += direction
                self.top_line += direction
                return
            self.cursor_y += direction
            return
        if direction == self.down_scroll:
            if self.cursor_y == self.bottom_line:
                return
            if self.cursor_y == self.top_line + self.max_lines - 1:
                self.top_line += direction
                self.cursor_y += direction
                return
            self.cursor_y += direction
            return

    def edit(self, char):
        if self.edited_position == 0:
            self.undo_stack.append(["edit", self.cursor_y, self.cursor_x,
                                    self.edited_array[self.cursor_y * self.columns + self.cursor_x]])
            self.edited_array[self.cursor_y * self.columns + self.cursor_x] =\
                str(char) + self.edited_array[self.cursor_y * self.columns + self.cursor_x][1]
            self.edited_position = 1
            self.changed = True
            return

        if self.edited_position == 1:
            self.undo_stack.append(["edit", self.cursor_y, self.cursor_x,
                                    self.edited_array[self.cursor_y * self.columns + self.cursor_x]])
            self.edited_array[self.cursor_y * self.columns + self.cursor_x] =\
                self.edited_array[self.cursor_y * self.columns + self.cursor_x][0] + str(char)
            self.edited_position = 0
            self.changed = True
            self.scroll_horizontally(self.right_scroll)
            return

    def clear_edit(self):
        no_edit = True
        for i, byte in enumerate(self.edited_array):
            x = i % self.columns
            y = i // self.columns
            if y == self.cursor_y and x == self.cursor_x:
                self.undo_stack.append(["edit", self.cursor_y, self.cursor_x,
                                        self.edited_array[self.cursor_y * self.columns + self.cursor_x]])
                self.edited_array[self.cursor_y * self.columns + self.cursor_x] = "--"
                self.scroll_horizontally(self.left_scroll)
                self.edited_position = 0
            elif byte != "--":
                no_edit = False
        if no_edit:
            self.changed = False

    def save(self):
        file_content = b''
        for i, byte in enumerate(self.file.content_array):
            edited_byte = self.edited_array[i]
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
