import sys, time, os, shutil
import select, termios
import config, ui

try:
    import pygame
    supported = True
    KEY_TO_ESCAPE_CODE = {
        pygame.K_UP: "\x1b[A", # up
        pygame.K_DOWN: "\x1b[B", # down
        pygame.K_RIGHT: "\x1b[C", # right
        pygame.K_LEFT: "\x1b[D" # left
    }
except Exception:
    supported = False

class PygameUI(ui.UI):
    def __init__(self):
        self.inital_options = None
        self.width = 40
        self.height = 30
        self.pixel_size = 25
        self.enable_beep = False
        self.screen = None
        self.font = None
        beep = config.load("beep")
        if beep:
            self.enable_beep = beep["enabled"]

    def init(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.width * self.pixel_size, self.height * self.pixel_size))
        self.font = pygame.font.SysFont("courier", self.pixel_size)
        pygame.display.set_caption("Pytris")

    def quit(self):
        pygame.quit()

    def main_loop(self, menu, tps=60):
        try:
            clock = pygame.time.Clock()
            menu.init(self)
            while True:
                key = self.get_key(block=False)
                while key is not None:
                    menu.key(key)
                    key = self.get_key(block=False)
                menu.tick()
                clock.tick(tps)
        except ui.ExitException:
            return

    def clear(self):
        self.screen.fill(ui.COLOURS[ui.COLOUR_BLACK])

    def draw_text(self, text, x, y, fg_colour=ui.COLOUR_WHITE, bg_colour=ui.COLOUR_BLACK):
        image = self.font.render(text, True, ui.COLOURS[fg_colour])
        rect = (x*self.pixel_size, y*self.pixel_size, image.get_width(), image.get_height())
        pygame.draw.rect(self.screen, ui.COLOURS[bg_colour], rect)
        self.screen.blit(image, (x*self.pixel_size, y*self.pixel_size))

    def set_pixel(self, colour, x, y):
        rect = (x*self.pixel_size, y*self.pixel_size, self.pixel_size, self.pixel_size)
        pygame.draw.rect(self.screen, ui.COLOURS[colour], rect)

    def beep(self):
        pass

    def update_screen(self):
        pygame.display.update()

    def menu(self, options, starting_option=0):
        menu = PygameMenu(options, starting_option)
        self.main_loop(menu)
        return menu.current

    def options_menu(self):
        options = ("Beep", "Close")
        while True:
            option = self.menu(options)
            if option == 0:
                self.enable_beep = self.menu(("Enable", "Disable"), starting_option = 0 if self.beep else 1) == 0
                config.save("beep", {"enabled": self.enable_beep})
            else:
                break

    def get_key(self, block=True):
        while True:
            event = pygame.event.poll()
            if event.type == pygame.KEYDOWN:
                if event.unicode == "\r":
                    return "\n"
                elif event.unicode:
                    return event.unicode
                return KEY_TO_ESCAPE_CODE.get(event.key, f"Key{event.scancode}")
            elif event.type == pygame.QUIT:
                raise ui.ExitException
            elif event.type == pygame.NOEVENT:
                if block:
                    continue
                else:
                    return None

class PygameMenu:
    def __init__(self, options, current):
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
        self.ui = None
    def init(self, ui):
        self.ui = ui
        self.resize(ui.width, ui.height)
    def resize(self, width, height):
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
    def key(self, c):
        self.ui.set_pixel(ui.COLOUR_BLACK, self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
        if c == '\x1b[A' or c == 'k':
            self.current -= 1
        elif c == '\x1b[B' or c == 'j':
            self.current += 1
        elif c == '\n' or c == ' ':
            raise ui.ExitException
        self.current %= self.n_options
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
    def tick(self):
        pass
