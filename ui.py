import enum
from typing import Collection, Union

class Colour(enum.Enum):
    BLACK    = 0
    WHITE    = 1
    GRAY     = 2
    RED      = 3
    ORANGE   = 4
    YELLOW   = 5
    GREEN    = 6
    BLUE     = 7
    CYAN     = 8
    MAGENTA  = 9

class Alignment(enum.Enum):
    LEFT = 0
    CENTER = 1

COLOURS = (
    (0, 0, 0),
    (255, 255, 255),
    (128, 128, 128),
    (188, 46, 61),
    (202, 99, 41),
    (253, 255, 12),
    (117, 174, 54),
    (55, 67, 190),
    (89, 154, 209),
    (155, 55, 134),
)

ASCII_TO_NAME = {
    " ": "Space",
    "\t": "Tab",
    "\n": "Return",
    "\r": "Return",
    "\x1b": "Escape",
    "\x7f": "Backspace"
}

ESCAPE_CODE_TO_NAME = {
    "\x1b[A": "Up",
    "\x1b[B": "Down",
    "\x1b[C": "Right",
    "\x1b[D": "Left",
    "\x1b[1~": "Home",
    "\x1b[2~": "Insert",
    "\x1b[3~": "Delete",
    "\x1b[4~": "End",
    "\x1b[5~": "Page Up",
    "\x1b[6~": "Page Down",
}

class ExitException(Exception):
    pass

class Menu:
    def init(self, ui: "UI") -> None: raise NotImplementedError
    def tick(self) -> None: raise NotImplementedError
    def key(self, c: str, repeated: bool = False) -> None: raise NotImplementedError
    def resize(self, width: int, height: int) -> None: raise NotImplementedError

class UI:
    width: int
    height: int
    def init(self) -> None: raise NotImplementedError
    def quit(self) -> None: raise NotImplementedError
    def draw_text(self, text: str, x: int, y: int, fg_colour: Colour = Colour.WHITE, bg_colour: Colour = Colour.BLACK, align: Alignment = Alignment.LEFT) -> None: raise NotImplementedError
    def set_pixel(self, colour: Colour, x: int, y: int) -> None: raise NotImplementedError
    def beep(self) -> None: raise NotImplementedError
    def clear(self) -> None: raise NotImplementedError
    def update_screen(self) -> None: raise NotImplementedError
    def main_loop(self, menu: Menu, tps: int = 10) -> None: raise NotImplementedError
    def menu(self, options: Collection[Union[str, Collection[str]]], starting_option: int = 0) -> int: raise NotImplementedError
    def get_key(self) -> str: raise NotImplementedError
    def options_menu(self) -> None: raise NotImplementedError
