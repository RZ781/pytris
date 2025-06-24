import ui
from typing import Sequence, Union

class MenuOption:
    def init(self, ui: ui.UI) -> None: raise NotImplementedError
    def get_name(self) -> str: raise NotImplementedError
    def key_pressed(self, key: str) -> None: raise NotImplementedError

class Button(MenuOption):
    name: str
    def init(self, ui: ui.UI) -> None:
        self.ui = ui
    def get_name(self) -> str:
        return self.name
    def key_pressed(self, key: str) -> None:
        if key == "Space" or key == "Return":
            self.click()
    def click(self) -> None: raise NotImplementedError

class Submenu(Button):
    def __init__(self, name: str, menu: ui.Menu) -> None:
        self.name = name
        self.menu = menu
    def get_name(self) -> str:
        return self.name
    def click(self) -> None:
        self.ui.push_menu(self.menu)

class Selection(Button):
    def __init__(self, name: str) -> None:
        self.name = name
    def get_name(self) -> str:
        return self.name
    def click(self) -> None:
        self.ui.pop_menu()

class Menu(ui.Menu):
    def __init__(self, options: Sequence[MenuOption]) -> None:
        self.columns = [options]
        self.n_options = len(options)
        length = max(len(option.get_name()) for option in options)
        self.current = 0

    def init(self, ui: ui.UI) -> None:
        self.ui = ui
        self.resize(ui.width, ui.height)
        for option in self.columns[0]:
            option.init(ui)

    def resize(self, width: int, height: int) -> None:
        self.ui.clear()
        text_width = max(max(len(x.get_name())//2 + 4 for x in column) for column in self.columns)
        self.menu_x = (width - text_width) // 2
        self.menu_y = height // 5
        column_x = self.menu_x + 1
        for column in self.columns:
            for i, option in enumerate(column):
                self.ui.draw_text(option.get_name(), column_x, self.menu_y+i)
            max_length = max(len(option.get_name()) for option in column)
            column_x += max_length // 2 + 4
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()

    def key(self, c: str, repeated: bool = False) -> None:
        self.ui.set_pixel(ui.Colour.BLACK, self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
        if c == "Up":
            self.current -= 1
        elif c == "Down":
            self.current += 1
        else:
            self.columns[0][self.current].key_pressed(c)
        self.current %= self.n_options
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()

    def tick(self) -> None:
        pass
