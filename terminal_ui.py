import sys, time, os, shutil, select
import config, ui, menu
from typing import Optional, Collection, Union, List

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

COLOURS_4_BIT = {
    ui.Colour.BLACK: 0,
    ui.Colour.WHITE: 7,
    ui.Colour.LIGHT_GREY: 8,
    ui.Colour.DARK_GREY: 8,
    ui.Colour.RED: 1,
    ui.Colour.BRIGHT_RED: 9,
    ui.Colour.ORANGE: 3,
    ui.Colour.YELLOW: 11,
    ui.Colour.GREEN: 10,
    ui.Colour.BLUE: 4,
    ui.Colour.CYAN: 6,
    ui.Colour.MAGENTA: 5
}

COLOURS_8_BIT = {
    ui.Colour.BLACK: 232,
    ui.Colour.WHITE: 255,
    ui.Colour.LIGHT_GREY: 246,
    ui.Colour.DARK_GREY: 241,
    ui.Colour.RED: 160,
    ui.Colour.BRIGHT_RED: 196,
    ui.Colour.ORANGE: 166,
    ui.Colour.YELLOW: 226,
    ui.Colour.GREEN: 118,
    ui.Colour.BLUE: 21,
    ui.Colour.CYAN: 45,
    ui.Colour.MAGENTA: 129,
}

class BeepSelection(menu.Button):
    def __init__(self, name: str, value: bool) -> None:
        self.name = [name]
        self.value = value
    def click(self) -> None:
        self.ui.pop_menu()
        config.save("beep", {"enabled": self.value})

class ModeSelection(menu.Button):
    def __init__(self, name: str) -> None:
        self.name = [name]
        self.value = name
    def click(self) -> None:
        self.ui.pop_menu()
        config.save("colours", {"mode": self.value})

class BaseTerminalUI(ui.UI):
    MODES = ["4 bit", "8 bit", "24 bit", "Monochrome"]
    fg_colour_codes = [
        {c: f"\x1b[38;5;{COLOURS_4_BIT[c]}m" for c in ui.Colour}, # 4 bit
        {c: f"\x1b[38;5;{COLOURS_8_BIT[c]}m" for c in ui.Colour}, # 8 bit
        {c: f"\x1b[38;2;{r};{g};{b}m" for c, (r, g, b) in ui.COLOURS.items()}, # 24 bit
        {c: "" for c in ui.Colour}, # monochrome
    ]
    bg_colour_codes = [
        {c: f"\x1b[48;5;{COLOURS_4_BIT[c]}m" for c in ui.Colour}, # 4 bit
        {c: f"\x1b[48;5;{COLOURS_8_BIT[c]}m" for c in ui.Colour}, # 8 bit
        {c: f"\x1b[48;2;{r};{g};{b}m" for c, (r, g, b) in ui.COLOURS.items()}, # 24 bit
        {c: "\x1b[0m" if c == ui.Colour.BLACK else "\x1b[7m" for c in ui.Colour}, # monochrome
    ]
    reset_code = "\x1b[0m"
    menus: List[ui.Menu]

    def __init__(self) -> None:
        self.menus = []
        self.fg_colour = ui.Colour.WHITE
        self.bg_colour = ui.Colour.BLACK
        self.buffer = ""
        self.inital_options = None
        terminal_size = shutil.get_terminal_size()
        self.width = terminal_size.columns // 2
        self.height = terminal_size.lines
        self.mode_menu = menu.Menu([ModeSelection(mode) for mode in BaseTerminalUI.MODES])
        self.beep_menu = menu.Menu([
            BeepSelection("Enable", True),
            BeepSelection("Disable", False)
        ])
        self.options_menu = menu.Menu([
            menu.Submenu("Colours", self.mode_menu),
            menu.Submenu("Beep", self.beep_menu),
            menu.Selection("Close")
        ])
        beep = config.load("beep")
        if beep:
            self.beep_menu.current = 0 if beep["enabled"] else 1
        else:
            self.beep_menu.current = 1
        self.mode = self.detect_colour_mode()
        colour_mode = config.load("colours")
        if colour_mode:
            mode = colour_mode["mode"]
            if mode in BaseTerminalUI.MODES:
                self.mode = BaseTerminalUI.MODES.index(mode)
        self.mode_menu.current = self.mode

    def main_loop(self, tps: int = 60) -> None:
        self.clear()
        self.update_screen()
        time_left = 1/tps
        prev_menu = None
        start_time = time.perf_counter()
        while len(self.menus) > 0:
            menu = self.menus[-1]
            if menu is not prev_menu:
                menu.resize(self.width, self.height)
            terminal_size = shutil.get_terminal_size()
            width = terminal_size.columns // 2
            height = terminal_size.lines
            if width != self.width or height != self.height:
                self.width = width
                self.height = height
                menu.resize(width, height)
            if self.check_keyboard_and_wait(time_left):
                menu.key(self.get_key())
            end_time = time.perf_counter()
            time_left -= end_time - start_time
            start_time = end_time
            while time_left < 0:
                time_left += 1/tps
                menu.tick()
            prev_menu = menu

    def push_menu(self, menu: ui.Menu) -> None:
        self.menus.append(menu)
        menu.init(self)

    def pop_menu(self) -> None:
        self.menus.pop()

    def clear(self) -> None:
        self.buffer += "\x1b[0m\x1b[2J\x1b[3J"

    def set_fg_colour(self, colour: ui.Colour) -> None:
        if colour != self.fg_colour:
            if colour == ui.Colour.WHITE:
                self.buffer += TerminalUI.reset_code
                # set background colour again if resetting terminal for foreground
                old_bg_colour = self.bg_colour
                self.fg_colour = ui.Colour.WHITE
                self.bg_colour = ui.Colour.BLACK
                self.set_bg_colour(old_bg_colour)
            else:
                self.buffer += TerminalUI.fg_colour_codes[self.mode_menu.current][colour]
                self.fg_colour = colour

    def set_bg_colour(self, colour: ui.Colour) -> None:
        if colour != self.bg_colour:
            if colour == ui.Colour.BLACK:
                self.buffer += TerminalUI.reset_code
                # set foreground colour again if resetting terminal for background
                old_fg_colour = self.fg_colour
                self.fg_colour = ui.Colour.WHITE
                self.bg_colour = ui.Colour.BLACK
                self.set_fg_colour(old_fg_colour)
            else:
                self.buffer += TerminalUI.bg_colour_codes[self.mode_menu.current][colour]
                self.bg_colour = colour

    def goto(self, x: float, y: float) -> None:
        self.buffer += f"\x1b[{int(y+1)};{int(2*x+1)}H" # double x so pixels are approximately square

    def draw_text(self, text: str, x: int, y: int, fg_colour: ui.Colour = ui.Colour.WHITE, bg_colour: ui.Colour = ui.Colour.BLACK, align: ui.Alignment = ui.Alignment.LEFT) -> None:
        if align == ui.Alignment.CENTER:
            offset = -len(text) / 4
        else:
            offset = 0
        self.set_fg_colour(fg_colour)
        self.set_bg_colour(bg_colour)
        self.goto(x+offset, y)
        self.buffer += text

    def set_pixel(self, colour: ui.Colour, x: int, y: int) -> None:
        self.goto(x, y)
        if self.mode_menu.current == 3 and colour == ui.Colour.LIGHT_GREY:
            self.set_bg_colour(ui.Colour.BLACK)
            self.buffer += "''"
        elif self.mode_menu.current == 3 and colour == ui.Colour.WHITE:
            self.set_bg_colour(ui.Colour.BLACK)
            self.buffer += "##"
        else:
            self.set_bg_colour(colour)
            self.buffer += "  "

    def beep(self) -> None:
        if self.beep_menu.current == 0:
            self.buffer += "\x07"

    def update_screen(self) -> None:
        self.goto(0, 0)
        sys.stdout.write(self.buffer)
        sys.stdout.flush()
        self.buffer = ""

    def get_options_menu(self) -> menu.Menu:
        return self.options_menu

    def get_key(self) -> str: raise NotImplementedError
    def detect_colour_mode(self) -> int: raise NotImplementedError
    def check_keyboard_and_wait(self, t: float) -> bool: raise NotImplementedError

if sys.platform == "win32":
    import msvcrt

    class TerminalUI(BaseTerminalUI):
        def init(self) -> None:
            pass

        def quit(self) -> None:
            self.set_fg_colour(ui.Colour.WHITE)
            self.set_bg_colour(ui.Colour.BLACK)
            self.goto(0, 0)
            self.update_screen()

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

        def check_keyboard_and_wait(self, t: float) -> bool:
            time.sleep(t)
            return msvcrt.kbhit()

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
            self.set_fg_colour(ui.Colour.WHITE)
            self.set_bg_colour(ui.Colour.BLACK)
            self.goto(0, 0)
            self.update_screen()

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

        def check_keyboard_and_wait(self, t: float) -> bool:
            r, _, _ = select.select([0], [], [], t)
            return len(r) != 0
