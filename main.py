#!/usr/bin/env python3
import sys, time
import game, ui, config, multiplayer, menu

CONTROL_NAMES = ("Left", "Right", "Soft Drop", "Hard Drop", "Rotate", "Rotate Clockwise", "Rotate Anticlockwise", "Rotate 180", "Hold", "Forfeit")

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
    def __init__(self) -> None:
        self.name = "Play"
    def click(self) -> None:
        randomiser: game.Randomiser = (
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
        x = game.Game(randomiser, 10, 20, game.GarbageType.NONE, True, None)
        x.set_objective(objective_type, objective_count)
        x.set_controls(controls, soft_drop_menu.current == 0, game.HoldType(hold_menu.current))
        x.set_spins(game.SpinType.SPIN, game.SpinType.MINI, game.SpinType.NONE, game.SpinType.NONE)
        spin_type = [2, 1, 0, 0] # t spins, mini t spins, immobile t pieces, immobile pieces
        main_ui.push_menu(x)

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
    menu.Selection("Enable"),
    menu.Selection("Disable")
])

hold_menu = menu.Menu([
    menu.Selection("No Hold"),
    menu.Selection("Normal"),
    menu.Selection("Infinite Hold"),
])

main_menu = menu.Menu([
    PlayButton(),
    menu.Submenu("Objectives", objective_menu),
    menu.Submenu("Bag Type", bag_type_menu),
    menu.Submenu("Infinite Soft Drop", soft_drop_menu),
    menu.Submenu("Hold", hold_menu)
])

try:
    main_ui.init()
    main_ui.push_menu(main_menu)
    main_ui.main_loop()
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
