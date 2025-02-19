import sys, select, termios, time, os

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

class UI:
    def draw_text(self, text, x, y, fg_colour=COLOUR_WHITE, bg_colour=COLOUR_BLACK): raise NotImplementedError
    def set_pixel(self, colour, x, y): raise NotImplementedError
    def update_screen(self): raise NotImplementedError
    def main_loop(self, tick_callback, key_callback): raise NotImplementedError

class TerminalUI(UI):
    fg_colour_codes = [f"\x1b[3{x}m" for x in range(8)] + [f"\x1b[9{x}m" for x in range(8)] + ["\x1b[0m"]
    bg_colour_codes = [f"\x1b[4{x}m" for x in range(8)] + [f"\x1b[10{x}m" for x in range(8)] + ["\x1b[0m"]
    def __init__(self):
        self.prev_fg_colour = None
        self.prev_bg_colour = None
        self.buffer = ""
        self.initial_options = termios.tcgetattr(0)
        self.set_fg_colour(COLOUR_WHITE)
        self.set_bg_colour(COLOUR_BLACK)
        self.update_screen()
        os.system("clear")
    def set_fg_colour(self, colour):
        if colour != self.prev_fg_colour:
            self.buffer += TerminalUI.fg_colour_codes[colour]
            self.prev_fg_colour = colour
    def set_bg_colour(self, colour):
        if colour != self.prev_bg_colour:
            self.buffer += TerminalUI.bg_colour_codes[colour]
            self.prev_bg_colour = colour
    def goto(self, x, y):
        self.buffer += f"\x1b[{y+1};{x+1}H"
    def draw_text(self, text, x, y, fg_colour=COLOUR_WHITE, bg_colour=COLOUR_BLACK):
        self.set_fg_colour(fg_colour)
        self.set_bg_colour(bg_colour)
        self.goto(x, y)
        self.buffer += text
    def set_pixel(self, colour, x, y):
        self.set_bg_colour(colour)
        self.goto(x*2, y) # double x so pixels are approximately square
        self.buffer += "  "
    def update_screen(self):
        self.goto(0, 0)
        sys.stdout.write(self.buffer)
        sys.stdout.flush()
        self.buffer = ""
    def main_loop(self, tick_callback, key_callback, tps=10):
        try:
            # set up terminal options
            custom_options = self.initial_options.copy()
            custom_options[3] &= ~termios.ECHO
            custom_options[3] &= ~termios.ICANON
            termios.tcsetattr(0, termios.TCSANOW, custom_options)
            time_left = 1/tps
            while True:
                start_time = time.perf_counter()
                r, _, _ = select.select([0], [], [], time_left)
                end_time = time.perf_counter()
                time_left -= end_time - start_time
                if r:
                    key_callback(os.read(0, 100))
                while time_left < 0:
                    time_left += 1/tps
                    tick_callback()
        finally:
            # reset terminal options
            termios.tcsetattr(0, termios.TCSANOW, self.initial_options)
            # reset terminal
            self.set_fg_colour(COLOUR_WHITE)
            self.set_bg_colour(COLOUR_BLACK)
            self.goto(0, 0)
            self.update_screen()
