import ui
from typing import Sequence, Union

class MenuOption:
    def init(self, ui: ui.UI, menu: "Menu") -> None: raise NotImplementedError
    def get_name(self) -> Sequence[str]: raise NotImplementedError
    def key_pressed(self, key: str, repeated: bool) -> None: raise NotImplementedError

class Button(MenuOption):
    name: Sequence[str]
    def init(self, ui: ui.UI, menu: "Menu") -> None:
        self.ui = ui
        self.menu = menu
    def get_name(self) -> Sequence[str]:
        return self.name
    def key_pressed(self, key: str, repeated: bool) -> None:
        if repeated:
            return
        if key == "Space" or key == "Return":
            self.click()
    def click(self) -> None: raise NotImplementedError

class Submenu(Button):
    def __init__(self, name: str, menu: ui.Menu) -> None:
        self.option_name = name
        self.submenu = menu
    def get_name(self) -> Sequence[str]:
        return [self.option_name]
    def click(self) -> None:
        self.ui.push_menu(self.submenu)

class PreviewSubmenu(Button):
    def __init__(self, name: str, menu: "Menu") -> None:
        self.option_name = name
        self.submenu = menu
    def get_name(self) -> Sequence[str]:
        current_option = self.submenu.options[self.submenu.current]
        return [self.option_name] + list(current_option.get_name())
    def click(self) -> None:
        self.ui.push_menu(self.submenu)

class Selection(Button):
    def __init__(self, name: str) -> None:
        self.name = [name]
    def click(self) -> None:
        self.ui.pop_menu()

class NumberSelector(MenuOption):
    def __init__(self, name: str, value: int, minimum: int, maximum: int, formatting: str):
        self.name = name
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        self.formatting = formatting
    def init(self, ui: ui.UI, menu: "Menu") -> None:
        self.ui = ui
        self.menu = menu
    def get_name(self) -> Sequence[str]:
        return [self.name, self.formatting.format(self.value)]
    def key_pressed(self, key: str, repeated: bool) -> None:
        if key == "Left" and self.value > self.minimum:
            self.value -= 1
        elif key == "Right" and self.value < self.maximum:
            self.value += 1
        elif key == "Space" or key == "Return":
            self.menu.set_info_text("Adjust value with left and right")
        self.menu.resize(self.ui.width, self.ui.height)

class Menu(ui.Menu):
    def __init__(self, options: Sequence[MenuOption], current: int = 0) -> None:
        self.options = options
        self.n_options = len(options)
        self.current = current
        self.info_text = ""
        self.info_text_ticks = 0

    def enable_custom_handling(self) -> bool:
        return False

    def init(self, ui: ui.UI) -> None:
        self.ui = ui
        for option in self.options:
            option.init(ui, self)

    def resize(self, width: int, height: int) -> None:
        self.ui.clear()
        if self.info_text_ticks == 120:
            self.ui.draw_text(self.info_text, self.ui.width//2, self.ui.height//5 - 2, align=ui.Alignment.CENTER)
        else:
            self.info_text_ticks = 0
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
            self.options[self.current].key_pressed(c, repeated)
        self.current %= self.n_options
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()

    def tick(self) -> None:
        self.info_text_ticks -= 1
        if self.info_text_ticks == 0:
            self.info_text = ""
            self.resize(self.ui.width, self.ui.height)

    def set_info_text(self, text: str) -> None:
        self.info_text = text
        self.info_text_ticks = 120
