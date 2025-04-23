COLOUR_BLACK    = 0
COLOUR_RED      = 1
COLOUR_GREEN    = 2
COLOUR_YELLOW   = 3
COLOUR_BLUE     = 4
COLOUR_MAGENTA  = 5
COLOUR_CYAN     = 6
COLOUR_WHITE    = 7

COLOUR_BRIGHT_BLACK    = 8
COLOUR_BRIGHT_RED      = 9
COLOUR_BRIGHT_GREEN    = 10
COLOUR_BRIGHT_YELLOW   = 11
COLOUR_BRIGHT_BLUE     = 12
COLOUR_BRIGHT_MAGENTA  = 13
COLOUR_BRIGHT_CYAN     = 14
COLOUR_BRIGHT_WHITE    = 15

COLOURS = (
    (0, 0, 0),
    (188, 46, 61),
    (8, 148, 24),
    (202, 99, 41),
    (55, 67, 190),
    (155, 55, 134),
    (89, 154, 209),
    (255, 255, 255),
    (128, 128, 128),
    (237, 28, 36),
    (117, 174, 54),
    (253, 255, 12),
    (4, 42, 255),
    (196, 6, 255),
    (8, 254, 255),
    (255, 255, 255),
)

class ExitException(Exception):
    pass

class Menu:
    def init(self, ui): raise NotImplementedError
    def tick(self): raise NotImplementedError
    def key(self, c): raise NotImplementedError
    def resize(self, width, height): raise NotImplementedError

class UI:
    def init(self): raise NotImplementedError
    def quit(self): raise NotImplementedError
    def draw_text(self, text, x, y, fg_colour=COLOUR_WHITE, bg_colour=COLOUR_BLACK): raise NotImplementedError
    def set_pixel(self, colour, x, y): raise NotImplementedError
    def beep(self): raise NotImplementedError
    def update_screen(self): raise NotImplementedError
    def main_loop(self, menu, tps=10): raise NotImplementedError
    def menu(self, options, starting_option=0): raise NotImplementedError
    def get_key(self): raise NotImplementedError
    def options_menu(self): raise NotImplementedError
