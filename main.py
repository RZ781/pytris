#!/usr/bin/env python3
import sys, time
import game, ui, config, multiplayer, menu
from typing import Sequence

try:
    import pygame
    pygame_support = True
except Exception:
    pygame_support = False

terminal = False
server = False
for arg in sys.argv[1:]:
    if arg == "--terminal":
        terminal = True
    elif arg == "--server":
        server = True
    else:
        exit(f"Invalid argument {arg}")

if server:
    multiplayer.server()
    exit()

main_ui: ui.UI
if pygame_support and not terminal:
    import pygame_ui
    main_ui = pygame_ui.PygameUI()
else:
    import terminal_ui
    main_ui = terminal_ui.TerminalUI()

default_controls = {
    game.Key.LEFT: "Left",
    game.Key.RIGHT: "Right",
    game.Key.SOFT_DROP: "Down",
    game.Key.HARD_DROP: "Space",
    game.Key.ROTATE: "Up",
    game.Key.CLOCKWISE: "x",
    game.Key.ANTICLOCKWISE: "z",
    game.Key.ROTATE_180: "a",
    game.Key.HOLD: "c",
    game.Key.FORFEIT: "Escape",
}

# version 1 of the config stored the keys directly in the json
# version 2+ has an attribute for the keys, infinite hold, and infinite soft drop
# version 1-2 use escape codes while version 3+ use key names
# version 4+ doesn't have infinite hold
controls_config = config.load("controls")
if controls_config and ("version" not in controls_config or 1 <= controls_config["version"] <= 4):
    if "version" in controls_config:
        version = controls_config["version"]
    else:
        version = 1
    if version == 1:
        keys = controls_config
    else:
        keys = controls_config["keys"]
    # json casts all keys to strings, so they must be converted back
    controls = {game.Key(int(a)): b for a, b in keys.items()}
    if version >= 2:
        infinite_soft_drop = controls_config["infinite_soft_drop"]
    # convert escape codes to key names
    if version < 3:
        for control, s in controls.items():
            if s in ui.ASCII_TO_NAME:
                controls[control] = ui.ASCII_TO_NAME[s]
            elif s in ui.ESCAPE_CODE_TO_NAME:
                controls[control] = ui.ESCAPE_CODE_TO_NAME[s]
    # add missing keys
    controls = default_controls | controls
else:
    controls = default_controls.copy()

controls_config = {
    "version": 4,
    "keys": {key.value: controls[key] for key in controls},
    "infinite_soft_drop": infinite_soft_drop
}

class PlayButton(menu.Button):
    def __init__(self, name, multiplayer=False) -> None:
        self.name = [name]
        self.multiplayer = multiplayer
    def click(self) -> None:
        randomiser: game.Randomiser
        if self.multiplayer:
            randomiser = game.BagRandomiser(1, 0)
            objective_type = game.Objective.NONE
            objective_count = 0
            board_width = 10
            board_height = 20
            garbage_type = game.GarbageType.NONE
            garbage_cancelling = True
            hold_type = game.HoldType.NORMAL
            spin_types = [game.SpinType.SPIN, game.SpinType.MINI, game.SpinType.NONE, game.SpinType.NONE]
            connection = multiplayer.connect_to_server()
            if connection is None:
                self.ui.draw_text("No server found", main_ui.width//2, main_ui.height//5 - 2, align=ui.Alignment.CENTER)
                self.ui.update_screen()
                return
        else:
            randomiser = (
                game.BagRandomiser(1, 0),
                game.BagRandomiser(2, 0),
                game.BagRandomiser(1, 1),
                game.BagRandomiser(1, 2),
                game.ClassicRandomiser()
            )[bag_type_menu.current]
            objective_type = (
                game.Objective.NONE,
                game.Objective.LINES,
                game.Objective.LINES,
                game.Objective.LINES,
                game.Objective.TIME,
                game.Objective.TIME
            )[objective_menu.current]
            objective_count = (0, 20, 40, 100, 60, 120)[objective_menu.current]
            board_width = (10, 4, 5, 20)[board_size_menu.current]
            board_height = (20, 24, 10, 20)[board_size_menu.current]
            connection = None
            garbage_type = game.GarbageType(garbage_menu.current)
            garbage_cancelling = garbage_cancelling_menu.current == 0
            hold_type = game.HoldType(hold_menu.current)
            spin_types = [game.SpinType(m.current) for m in spin_menus]
        x = game.Game(randomiser, board_width, board_height, garbage_type, garbage_cancelling, connection)
        x.set_objective(objective_type, objective_count)
        x.set_controls(controls, soft_drop_menu.current == 0, hold_type)
        x.set_spins(*spin_types)
        self.ui.push_menu(x)

class SoftDropSelection(menu.Button):
    def __init__(self, name: str) -> None:
        self.name = [name]
    def click(self) -> None:
        self.ui.pop_menu()
        controls_config["infinite_soft_drop"] = soft_drop_menu.current == 0
        config.save("controls", controls_config)

class ControlMenu(ui.Menu):
    def __init__(self, name: str, key: game.Key) -> None:
        self.name = name
        self.control = key
    def init(self, ui: ui.UI) -> None:
        self.ui = ui
    def resize(self, width: int, height: int) -> None:
        self.ui.draw_text(f"Press key for {self.name.lower()}", self.ui.width // 2, self.ui.height // 10, align=ui.Alignment.CENTER)
        self.ui.update_screen()
    def key(self, c: str, repeated: bool = False) -> None:
        if repeated:
            return
        controls[self.control] = c
        self.ui.pop_menu()
    def tick(self) -> None:
        pass

class ControlButton(menu.Submenu):
    def __init__(self, name: str, key: game.Key) -> None:
        self.control_name = name
        self.key = key
        self.menu = ControlMenu(name, key)
    def get_name(self) -> Sequence[str]:
        return [self.control_name, controls[self.key]]

class ControlsCloseButton(menu.Button):
    def __init__(self) -> None:
        self.name = ["Close"]
    def click(self) -> None:
        controls_config["keys"] = {key.value: controls[key] for key in controls}
        config.save("controls", controls_config)
        self.ui.pop_menu()

class PresetButton(menu.Button):
    def __init__(self, name: str, objective: int, bag_type: int, board_size: int, spin_types: Sequence[int], garbage_type: int, hold_type: int, garbage_cancelling: bool):
        self.name = [name]
        self.objective = objective
        self.bag_type = bag_type
        self.board_size = board_size
        self.spin_types = spin_types
        self.garbage_type = garbage_type
        self.hold_type = hold_type
        self.garbage_cancelling = garbage_cancelling
    def click(self) -> None:
        self.ui.pop_menu()
        objective_menu.current = self.objective
        bag_type_menu.current = self.bag_type
        board_size_menu.current = self.board_size
        for i, m in enumerate(spin_menus):
            m.current = self.spin_types[i]
        garbage_menu.current = self.garbage_type
        hold_menu.current = self.hold_type
        garbage_cancelling_menu.current = 0 if self.garbage_cancelling else 1

controls_menu = menu.Menu([
    ControlsCloseButton(),
    ControlButton("Left", game.Key.LEFT),
    ControlButton("Right", game.Key.RIGHT),
    ControlButton("Soft Drop", game.Key.SOFT_DROP),
    ControlButton("Hard Drop", game.Key.HARD_DROP),
    ControlButton("Rotate", game.Key.ROTATE),
    ControlButton("Rotate Clockwise", game.Key.CLOCKWISE),
    ControlButton("Rotate Anticlockwise", game.Key.ANTICLOCKWISE),
    ControlButton("Rotate 180", game.Key.ROTATE_180),
    ControlButton("Hold", game.Key.HOLD),
    ControlButton("Forfeit", game.Key.FORFEIT)
])

preset_menu = menu.Menu([
    PresetButton("Marathon", 0, 0, 0, [2, 1, 0, 0], 0, 1, True),
    PresetButton("Classic",  0, 4, 0, [0, 0, 0, 0], 0, 0, True),
    PresetButton("40 Lines", 2, 0, 0, [2, 1, 0, 0], 0, 1, True),
    PresetButton("Ultra",    5, 0, 0, [2, 1, 0, 0], 0, 1, True),
    PresetButton("Survival", 0, 0, 0, [2, 1, 0, 0], 2, 1, False),
    PresetButton("Big Mode", 0, 0, 2, [2, 1, 0, 1], 0, 1, True),
    PresetButton("4 Wide",   0, 0, 1, [2, 1, 0, 1], 0, 1, True),
    PresetButton("Chaos",    5, 1, 0, [2, 2, 2, 2], 5, 0, False),
])

objective_menu = menu.Menu([
    menu.Selection("None"),
    menu.Selection("20 lines"),
    menu.Selection("40 lines"),
    menu.Selection("100 lines"),
    menu.Selection("1 minutes"),
    menu.Selection("2 minutes")
])

bag_type_menu = menu.Menu([
    menu.Selection("7 bag"),
    menu.Selection("14 bag"),
    menu.Selection("7+1 bag"),
    menu.Selection("7+2 bag"),
    menu.Selection("Classic")
])

soft_drop_menu = menu.Menu([
    SoftDropSelection("Enable"),
    SoftDropSelection("Disable")
], 0 if infinite_soft_drop else 1)

hold_menu = menu.Menu([
    menu.Selection("No Hold"),
    menu.Selection("Normal"),
    menu.Selection("Infinite Hold")
], 1)

board_size_menu = menu.Menu([
    menu.Selection("Normal"),
    menu.Selection("4 Wide"),
    menu.Selection("Big Mode"),
    menu.Selection("Massive (20x20)")
])

garbage_menu = menu.Menu([
    menu.Selection("None"),
    menu.Selection("Slow Cheese"),
    menu.Selection("Fast Cheese"),
    menu.Selection("Slow Clean"),
    menu.Selection("Fast Clean"),
    menu.Selection("Backfire")
])

garbage_cancelling_menu = menu.Menu([
    menu.Selection("Enable"),
    menu.Selection("Disable")
])

spin_names = ("T Spin", "Mini T Spin", "Immobile T Piece", "Immobile Piece")
spin_menus = [menu.Menu([menu.Selection("None"), menu.Selection("Mini Spin"), menu.Selection("Full Spin")], default) for default in (2, 1, 0, 0)]

spin_type_menu = menu.Menu([menu.Selection("Close")] + [
    menu.Submenu(name, m) for name, m in zip(spin_names, spin_menus)
])

main_menu = menu.Menu([
    PlayButton("Play"),
    PlayButton("Multiplayer", multiplayer=True),
    menu.Submenu("Controls", controls_menu),
    menu.Submenu("Presets", preset_menu),
    menu.Submenu("Objectives", objective_menu, show_option=True),
    menu.Submenu("Bag Type", bag_type_menu, show_option=True),
    menu.Submenu("Infinite Soft Drop", soft_drop_menu, show_option=True),
    menu.Submenu("Hold", hold_menu, show_option=True),
    menu.Submenu("Board Size", board_size_menu, show_option=True),
    menu.Submenu("Garbage", garbage_menu, show_option=True),
    menu.Submenu("Garbage Cancelling", garbage_cancelling_menu, show_option=True),
    menu.Submenu("Spin Detection", spin_type_menu),
    menu.Selection("Quit")
])

try:
    main_ui.init()
    main_ui.push_menu(main_menu)
    main_ui.main_loop()
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
