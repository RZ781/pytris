import config, ui, pygame
from typing import Optional, Collection, Union, Dict

pygame.init()
KEY_TO_NAME = {
    pygame.K_UP: "Up",
    pygame.K_DOWN: "Down",
    pygame.K_RIGHT: "Right",
    pygame.K_LEFT: "Left"
}

ARR = 5
DAS = 12

def key_name(event):
    if event.unicode:
        return ui.ASCII_TO_NAME.get(event.unicode, event.unicode)
    return KEY_TO_NAME.get(event.key, f"Key{event.scancode}")

class PygameUI(ui.UI):
    screen: pygame.Surface
    font: pygame.font.Font
    keys: Dict[str, int]

    def __init__(self) -> None:
        self.inital_options = None
        self.width = 40
        self.height = 30
        self.pixel_size = 25
        self.enable_beep = False
        self.screen = pygame.display.set_mode((self.width * self.pixel_size, self.height * self.pixel_size))
        self.font = pygame.font.SysFont("courier", self.pixel_size)
        self.keys = {}
        beep = config.load("beep")
        if beep:
            self.enable_beep = beep["enabled"]

    def init(self) -> None:
        pygame.display.set_caption("Pytris")

    def quit(self) -> None:
        pygame.quit()

    def main_loop(self, menu: ui.Menu, tps: int = 60) -> None:
        try:
            clock = pygame.time.Clock()
            menu.init(self)
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        key = key_name(event)
                        self.keys[key] = 0
                    elif event.type == pygame.KEYUP:
                        self.keys.pop(key_name(event))
                    elif event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                for key, frame in self.keys.items():
                    if frame == 0 or (frame >= DAS and (frame - DAS) % ARR == 0):
                        menu.key(key)
                    self.keys[key] += 1
                menu.tick()
                clock.tick(tps)
        except ui.ExitException:
            return

    def clear(self) -> None:
        self.screen.fill(ui.COLOURS[ui.COLOUR_BLACK])

    def draw_text(self, text: str, x: int, y: int, fg_colour: int = ui.COLOUR_WHITE, bg_colour: int = ui.COLOUR_BLACK) -> None:
        image = self.font.render(text, True, ui.COLOURS[fg_colour])
        rect = (x*self.pixel_size, y*self.pixel_size, image.get_width(), image.get_height())
        pygame.draw.rect(self.screen, ui.COLOURS[bg_colour], rect)
        self.screen.blit(image, (x*self.pixel_size, y*self.pixel_size))

    def set_pixel(self, colour: int, x: int, y: int) -> None:
        rect = (x*self.pixel_size, y*self.pixel_size, self.pixel_size, self.pixel_size)
        pygame.draw.rect(self.screen, ui.COLOURS[colour], rect)

    def beep(self) -> None:
        pass

    def update_screen(self) -> None:
        pygame.display.update()

    def menu(self, options: Collection[Union[str, Collection[str]]], starting_option: int = 0) -> int:
        menu = PygameMenu(options, starting_option)
        self.main_loop(menu)
        return menu.current

    def options_menu(self) -> None:
        options = ("Beep", "Close")
        while True:
            option = self.menu(options)
            if option == 0:
                self.enable_beep = self.menu(("Enable", "Disable"), starting_option = 0 if self.enable_beep else 1) == 0
                config.save("beep", {"enabled": self.enable_beep})
            else:
                break

    def get_key_nonblocking(self) -> Optional[str]:
        while True:
            event = pygame.event.poll()
            if event.type == pygame.KEYDOWN:
                return key_name(event)
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.NOEVENT:
                return None

    def get_key(self) -> str:
        key = None
        while key is None:
            key = self.get_key_nonblocking()
        return key

class PygameMenu(ui.Menu):
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

    def key(self, c: str) -> None:
        self.ui.set_pixel(ui.COLOUR_BLACK, self.menu_x, self.menu_y + self.current)
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
