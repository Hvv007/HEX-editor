import curses


class Window:
    def __init__(self, stdscr, application):
        super(__class__, self).__init__()
        self.stdscr: curses.window = stdscr
        self.application: Application = application
        self.width = int
        self.height = int
        self.key_pressed = int

    def init_colors(self):
        """
        Инициализация цветов в окне
        Вызывается вручную
        """

    def update(self):
        """
        Вызывается каждый раз, когда Window обновляется
        В основном здесь считаются координаты для отрисовки
        """

    def late_update(self):
        """
        Вызывается каждый раз после функции update
        В основном здесь идёт отрисовка
        """

    def check_keys(self):
        """
        Проверка клавиш
        """

    def window_update(self):
        """
        Вызывается из Application и вызывает фунции для обновления
        """
        self.height, self.width = self.stdscr.getmaxyx()
        self.key_pressed = self.stdscr.getch()
        self.check_keys()
        self.update()
        self.stdscr.erase()
        self.late_update()
        self.update_screen()

    def update_screen(self):
        """
        Обновляет Экран
        """
        self.stdscr.refresh()

    def draw_text(self, y_coord, x_coord, text, color_code):
        """
        Функция отрисовки текста на экране
        """
        self.stdscr.attron(curses.A_BOLD)
        self.stdscr.attron(curses.color_pair(color_code))
        self.stdscr.addstr(y_coord, x_coord, text)
        self.stdscr.attroff(curses.A_BOLD)
        self.stdscr.attroff(curses.color_pair(color_code))

    def exit(self):
        """
        Эта функция вызовется при закрытии программы
        """

    @staticmethod
    def set_cursor_state(state: int):
        curses.curs_set(state)


class Application:
    def __init__(self):
        super(__class__, self).__init__()
        self.stdscr = curses.initscr()
        self.stdscr.keypad(True)
        self.window = None
        curses.noecho()
        curses.cbreak()

    def set_main_window(self, window: Window):
        self.window = window

    def run(self):
        self.window.height, self.window.width = self.stdscr.getmaxyx()
        self.window.update()
        self.stdscr.erase()
        self.window.late_update()
        self.window.update_screen()
        while True:
            self.window.window_update()
