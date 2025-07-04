import ui
from typing import Sequence, Union

class MenuOption:
    def init(self, ui: ui.UI) -> None: raise NotImplementedError
    def get_name(self) -> Sequence[str]: raise NotImplementedError
    def key_pressed(self, key: str) -> None: raise NotImplementedError

class Button(MenuOption):
    name: Sequence[str]
    def init(self, ui: ui.UI) -> None:
        self.ui = ui
    def get_name(self) -> Sequence[str]:
        return self.name
    def key_pressed(self, key: str) -> None:
        if key == "Space" or key == "Return":
            self.click()
    def click(self) -> None: raise NotImplementedError

class Submenu(Button):
    def __init__(self, name: str, menu: ui.Menu) -> None:
        self.name = [name]
        self.menu = menu
    def click(self) -> None:
        self.ui.push_menu(self.menu)

class Selection(Button):
    def __init__(self, name: str) -> None:
        self.name = [name]
    def click(self) -> None:
        self.ui.pop_menu()

class Menu(ui.Menu):
    def __init__(self, options: Sequence[MenuOption], current: int = 0) -> None:
        self.options = options
        self.n_options = len(options)
        self.current = current

    def init(self, ui: ui.UI) -> None:
        self.ui = ui
        self.resize(ui.width, ui.height)
        for option in self.options:
            option.init(ui)

    def resize(self, width: int, height: int) -> None:
        self.ui.clear()
        names = [list(option.get_name()) for option in self.options]
        max_row_length = max(len(name) for name in names)
        columns = []
        for i in range(max_row_length):
            column = [name[i] if i < len(name) else "" for name in names]
            columns.append(column)
        max_row_width = sum(max(len(x)//2+4 for x in column) for column in columns)
        self.menu_x = (width - max_row_width) // 2
        self.menu_y = height // 5
        column_x = self.menu_x + 1
        for column in columns:
            for i, option in enumerate(column):
                self.ui.draw_text(option, column_x, self.menu_y+i)
            max_length = max(len(option) for option in column)
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
            self.options[self.current].key_pressed(c)
        self.current %= self.n_options
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()

    def tick(self) -> None:
        pass
