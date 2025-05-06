import sys, time, os, shutil, socket, select
import config, ui
from typing import Optional, Collection, Union

SCANCODE_TO_NAME = {
    0x48: "Up",
    0x50: "Down",
    0x4D: "Right",
    0x4B: "Left",
    0x47: "Home",
    0x52: "Insert",
    0x53: "Delete",
    0x4F: "End",
    0x49: "Page Up",
    0x51: "Page Down",
    0x08: "Delete"
}

class BaseTerminalUI(ui.UI):
    MODES = ["4 bit", "8 bit", "24 bit", "Monochrome"]
    COLOURS_8_BIT = (232, 160, 40, 166, 21, 129, 45, 255, 243, 196, 118, 226, 27, 165, 51, 255)
    fg_colour_codes = [
        [f"\x1b[3{x}m" for x in range(7)] + [""] + [f"\x1b[9{x}m" for x in range(8)], # 4 bit
        [f"\x1b[38;5;{x}m" for x in COLOURS_8_BIT], # 8 bit
        [f"\x1b[38;2;{r};{g};{b}m" for r, g, b in ui.COLOURS], # 24 bit
        [""]*7 + ["\x1b[0m"] + [""]*8, # monochrome
    ]
    bg_colour_codes = [
        [""] + [f"\x1b[4{x}m" for x in range(1, 8)] + [f"\x1b[10{x}m" for x in range(8)], # 4 bit
        [f"\x1b[48;5;{x}m" for x in COLOURS_8_BIT], # 8 bit
        [f"\x1b[48;2;{r};{g};{b}m" for r, g, b in ui.COLOURS], # 24 bit
        ["\x1b[0m"] + ["\x1b[7m"]*15, # monochrome
    ]
    reset_code = "\x1b[0m"

    def __init__(self) -> None:
        self.fg_colour = ui.COLOUR_WHITE
        self.bg_colour = ui.COLOUR_BLACK
        self.buffer = ""
        self.inital_options = None
        terminal_size = shutil.get_terminal_size()
        self.width = terminal_size.columns // 2
        self.height = terminal_size.lines
        self.mode = self.detect_colour_mode()
        colour_mode = config.load("colours")
        if colour_mode:
            mode = colour_mode["mode"]
            if mode in BaseTerminalUI.MODES:
                self.mode = BaseTerminalUI.MODES.index(mode)
        self.enable_beep = False
        beep = config.load("beep")
        if beep:
            self.enable_beep = beep["enabled"]

    def clear(self) -> None:
        self.buffer += "\x1b[0m\x1b[2J\x1b[3J"

    def set_fg_colour(self, colour: int) -> None:
        if colour != self.fg_colour:
            if colour == ui.COLOUR_WHITE:
                self.buffer += TerminalUI.reset_code
                # set background colour again if resetting terminal for foreground
                old_bg_colour = self.bg_colour
                self.fg_colour = ui.COLOUR_WHITE
                self.bg_colour = ui.COLOUR_BLACK
                self.set_bg_colour(old_bg_colour)
            else:
                self.buffer += TerminalUI.fg_colour_codes[self.mode][colour]
                self.fg_colour = colour

    def set_bg_colour(self, colour: int) -> None:
        if colour != self.bg_colour:
            if colour == ui.COLOUR_BLACK:
                self.buffer += TerminalUI.reset_code
                # set foreground colour again if resetting terminal for background
                old_fg_colour = self.fg_colour
                self.fg_colour = ui.COLOUR_WHITE
                self.bg_colour = ui.COLOUR_BLACK
                self.set_fg_colour(old_fg_colour)
            else:
                self.buffer += TerminalUI.bg_colour_codes[self.mode][colour]
                self.bg_colour = colour

    def goto(self, x: float, y: float) -> None:
        self.buffer += f"\x1b[{int(y+1)};{int(2*x+1)}H" # double x so pixels are approximately square

    def draw_text(self, text: str, x: int, y: int, fg_colour: int = ui.COLOUR_WHITE, bg_colour: int = ui.COLOUR_BLACK, align: int = ui.ALIGN_LEFT) -> None:
        if align == ui.ALIGN_CENTER:
            offset = -len(text) / 4
        else:
            offset = 0
        self.set_fg_colour(fg_colour)
        self.set_bg_colour(bg_colour)
        self.goto(x+offset, y)
        self.buffer += text

    def set_pixel(self, colour: int, x: int, y: int) -> None:
        self.goto(x, y)
        if self.mode == 3 and colour == ui.COLOUR_BRIGHT_BLACK:
            self.set_bg_colour(ui.COLOUR_BLACK)
            self.buffer += "''"
        elif self.mode == 3 and colour == ui.COLOUR_WHITE:
            self.set_bg_colour(ui.COLOUR_BLACK)
            self.buffer += "##"
        else:
            self.set_bg_colour(colour)
            self.buffer += "  "

    def beep(self) -> None:
        if self.enable_beep:
            self.buffer += "\x07"

    def update_screen(self) -> None:
        self.goto(0, 0)
        sys.stdout.write(self.buffer)
        sys.stdout.flush()
        self.buffer = ""

    def menu(self, options: Collection[Union[str, Collection[str]]], starting_option: int = 0) -> int:
        menu = TerminalMenu(options, starting_option)
        self.main_loop(menu)
        return menu.current

    def options_menu(self) -> None:
        options = ("Colours", "Beep", "Close")
        while True:
            option = self.menu(options)
            if option == 0:
                self.mode = self.menu(BaseTerminalUI.MODES, starting_option=self.mode)
                config.save("colours", {"mode": BaseTerminalUI.MODES[self.mode]})
            elif option == 1:
                self.enable_beep = self.menu(("Enable", "Disable"), starting_option = 0 if self.enable_beep else 1) == 0
                config.save("beep", {"enabled": self.enable_beep})
            else:
                break

    def get_key(self) -> str: raise NotImplementedError
    def detect_colour_mode(self) -> int: raise NotImplementedError

class TerminalMenu(ui.Menu):
    def __init__(self, options: Collection[Union[str, Collection[str]]], current: int) -> None:
        self.columns = []
        self.n_options = len(options)
        length = max(len(option) for option in options)
        for i in range(length):
            column = []
            for option in options:
                if isinstance(option, str) and i == 0:
                    column.append(option)
                elif isinstance(option, tuple) and i < len(option):
                    column.append(option[i])
                else:
                    column.append("")
            self.columns.append(column)
        self.current = current

    def init(self, ui: ui.UI) -> None:
        self.ui = ui
        self.resize(ui.width, ui.height)

    def resize(self, width: int, height: int) -> None:
        self.ui.clear()
        text_width = max(max(len(x)//2 + 4 for x in column) for column in self.columns)
        self.menu_x = (width - text_width) // 2
        self.menu_y = height // 5
        column_x = self.menu_x + 1
        for column in self.columns:
            for i, option in enumerate(column):
                self.ui.draw_text(option, column_x, self.menu_y+i)
            max_length = max(len(option) for option in column)
            column_x += max_length // 2 + 4
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()

    def key(self, c: str, repeated: bool = False) -> None:
        self.ui.draw_text(" ", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
        if c == "Up" or c == 'k':
            self.current -= 1
        elif c == "Down" or c == 'j':
            self.current += 1
        elif c == "Return" or c == "Space":
            raise ui.ExitException
        self.current %= self.n_options
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()

    def tick(self) -> None:
        pass

if sys.platform == "win32":
    import msvcrt

    class TerminalUI(BaseTerminalUI):
        def init(self) -> None:
            pass

        def quit(self) -> None:
            self.set_fg_colour(ui.COLOUR_WHITE)
            self.set_bg_colour(ui.COLOUR_BLACK)
            self.goto(0, 0)
            self.update_screen()

        def main_loop(self, menu: ui.Menu, tps: int = 60) -> None:
            try:
                self.clear()
                self.update_screen()
                menu.init(self)
                while True:
                    terminal_size = shutil.get_terminal_size()
                    width = terminal_size.columns // 2
                    height = terminal_size.lines
                    if width != self.width or height != self.height:
                        self.width = width
                        self.height = height
                        menu.resize(width, height)
                    end_time = time.perf_counter()
                    if msvcrt.kbhit():
                        menu.key(self.get_key())
                    menu.tick()
                    time.sleep(1/tps)
            except ui.ExitException:
                return

        def get_key(self) -> str:
            c = msvcrt.getch()
            if c == b'\xe0' or c == b'\x00':
                scancode = msvcrt.getch()[0]
                s = f"Scancode{scancode}"
                return SCANCODE_TO_NAME.get(scancode, s)
            else:
                s = chr(c[0])
                return ui.ASCII_TO_NAME.get(s, s)

        def detect_colour_mode(self) -> int:
            return 1

else:
    import termios
    class TerminalUI(BaseTerminalUI):
        def init(self) -> None:
            # update terminal options
            self.initial_options = termios.tcgetattr(0)
            custom_options = self.initial_options.copy()
            custom_options[3] &= ~termios.ECHO
            custom_options[3] &= ~termios.ICANON
            termios.tcsetattr(0, termios.TCSANOW, custom_options)

        def quit(self) -> None:
            # reset terminal options
            termios.tcsetattr(0, termios.TCSANOW, self.initial_options)
            # reset terminal
            self.set_fg_colour(ui.COLOUR_WHITE)
            self.set_bg_colour(ui.COLOUR_BLACK)
            self.goto(0, 0)
            self.update_screen()

        def main_loop(self, menu: ui.Menu, tps: int = 60) -> None:
            try:
                self.clear()
                self.update_screen()
                menu.init(self)
                time_left = 1/tps
                while True:
                    start_time = time.perf_counter()
                    r, _, _ = select.select([0], [], [], time_left)
                    terminal_size = shutil.get_terminal_size()
                    width = terminal_size.columns // 2
                    height = terminal_size.lines
                    if width != self.width or height != self.height:
                        self.width = width
                        self.height = height
                        menu.resize(width, height)
                    end_time = time.perf_counter()
                    time_left -= end_time - start_time
                    if r:
                        menu.key(self.get_key())
                    while time_left < 0:
                        time_left += 1/tps
                        menu.tick()
            except ui.ExitException:
                return

        def get_key(self) -> str:
            s = os.read(0, 100).decode("utf8")
            if s in ui.ESCAPE_CODE_TO_NAME:
                return ui.ESCAPE_CODE_TO_NAME[s];
            return ui.ASCII_TO_NAME.get(s, s);

        def detect_colour_mode(self) -> int:
            terminal = os.environ.get("TERM", "")
            colour = os.environ.get("COLORTERM", "")
            if "256color" in terminal:
                return 1
            elif colour == "24bit" or colour == "truecolor":
                return 2
            else:
                return 0
