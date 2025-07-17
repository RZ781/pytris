import config, ui, pygame, menu
from typing import Optional, Collection, Union, Dict, List

pygame.init()
KEY_TO_NAME = {
    pygame.K_UP: "Up",
    pygame.K_DOWN: "Down",
    pygame.K_RIGHT: "Right",
    pygame.K_LEFT: "Left"
}

ARR = 4
DAS = 10

def key_name(event: pygame.event.Event) -> str:
    if event.unicode:
        return ui.ASCII_TO_NAME.get(event.unicode, event.unicode)
    return KEY_TO_NAME.get(event.key, f"Key{event.scancode}")

class BeepSelection(menu.Button):
    def __init__(self, name: str, value: bool) -> None:
        self.name = [name]
        self.value = value
    def click(self) -> None:
        self.ui.pop_menu()
        config.save("beep", {"enabled": self.value})

class PygameUI(ui.UI):
    screen: pygame.Surface
    font: pygame.font.Font
    keys: Dict[str, int]
    menus: List[ui.Menu]

    def __init__(self) -> None:
        self.menus = []
        self.inital_options = None
        self.target_width = self.width = 40
        self.target_height = self.height = 32
        self.pixel_size = 25
        self.screen = pygame.display.set_mode((self.width * self.pixel_size, self.height * self.pixel_size), pygame.RESIZABLE)
        self.font = pygame.font.SysFont("courier", self.pixel_size)
        self.beep_menu = menu.Menu([
            BeepSelection("Enable", True),
            BeepSelection("Disable", False)
        ])
        self.options_menu = menu.Menu([
            menu.Submenu("Beep", self.beep_menu),
            menu.Selection("Close")
        ])
        beep = config.load("beep")
        if beep:
            self.beep_menu.current = 0 if beep["enabled"] else 1
        else:
            self.beep_menu.current = 1

    def init(self) -> None:
        pygame.display.set_caption("Pytris")

    def quit(self) -> None:
        pygame.quit()

    def main_loop(self, tps: int = 60) -> None:
        keys = {}
        clock = pygame.time.Clock()
        prev_menu = None
        while len(self.menus) > 0:
            menu = self.menus[-1]
            if menu is not prev_menu:
                menu.resize(self.width, self.height)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    key = key_name(event)
                    keys[key] = 0
                elif event.type == pygame.KEYUP:
                    name = key_name(event)
                    if name in keys:
                        keys.pop(name)
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.WINDOWRESIZED:
                    self.pixel_size = max(2, min(event.x // self.target_width, event.y // self.target_height))
                    self.width = event.x // self.pixel_size
                    self.height = event.y // self.pixel_size
                    self.font = pygame.font.SysFont("courier", self.pixel_size)
                    menu.resize(self.width, self.height)
            for key, frame in keys.items():
                if frame == 0:
                    menu.key(key)
                if frame >= DAS and (frame - DAS) % ARR == 0:
                    menu.key(key, repeated=True)
                keys[key] += 1
            menu.tick()
            clock.tick(tps)
            prev_menu = menu

    def push_menu(self, menu: ui.Menu) -> None:
        self.menus.append(menu)
        menu.init(self)

    def pop_menu(self) -> None:
        self.menus.pop()

    def clear(self) -> None:
        self.screen.fill(ui.COLOURS[ui.Colour.BLACK])

    def draw_text(self, text: str, x: int, y: int, fg_colour: ui.Colour = ui.Colour.WHITE, bg_colour: ui.Colour = ui.Colour.BLACK, align: ui.Alignment = ui.Alignment.LEFT) -> None:
        image = self.font.render(text, True, ui.COLOURS[fg_colour])
        pixel_x = x * self.pixel_size
        pixel_y = y * self.pixel_size
        if align == ui.Alignment.CENTER:
            pixel_x -= image.get_width() // 2
        rect = (pixel_x, pixel_y, image.get_width(), image.get_height())
        pygame.draw.rect(self.screen, ui.COLOURS[bg_colour], rect)
        self.screen.blit(image, (pixel_x, pixel_y))

    def set_pixel(self, colour: ui.Colour, x: int, y: int) -> None:
        rect = (x*self.pixel_size, y*self.pixel_size, self.pixel_size, self.pixel_size)
        pygame.draw.rect(self.screen, ui.COLOURS[colour], rect)

    def beep(self) -> None:
        pass

    def update_screen(self) -> None:
        pygame.display.update()

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

    def get_options_menu(self) -> menu.Menu:
        return self.options_menu
