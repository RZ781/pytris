#!/usr/bin/env python3
import sys
import game, ui, config, terminal_ui

CONTROL_NAMES = ("Left", "Right", "Soft Drop", "Hard Drop", "Rotate", "Rotate Clockwise", "Rotate Anticlockwise", "Rotate 180", "Hold")

main_ui: ui.UI
try:
    import pygame
    pygame_support = True
except Exception:
    pygame_support = False

if pygame_support and "--terminal" not in sys.argv:
    import pygame_ui
    main_ui = pygame_ui.PygameUI()
else:
    main_ui = terminal_ui.TerminalUI()

bag_type = 0
objective = game.OBJECTIVE_NONE
infinite_soft_drop = False
infinite_hold = False

default_controls = {
    game.KEY_LEFT: "Left",
    game.KEY_RIGHT: "Right",
    game.KEY_SOFT_DROP: "Down",
    game.KEY_HARD_DROP: "Space",
    game.KEY_ROTATE: "Up",
    game.KEY_CLOCKWISE: "x",
    game.KEY_ANTICLOCKWISE: "z",
    game.KEY_180: "a",
    game.KEY_HOLD: "c",
}

# version 1 of the config stored the keys directly in the json
# version 2 and 3 stores has an attribute for the keys, infinite hold, and infinite soft drop
# version 1 and 2 use escape codes while version 3 use key names
controls_config = config.load("controls")
if controls_config and ("version" not in controls_config or 1 <= controls_config["version"] <= 3):
    if "version" in controls_config:
        version = controls_config["version"]
    else:
        version = 1
    if version == 1:
        keys = controls_config
    else:
        keys = controls_config["keys"]
    # json casts all keys to strings, so they must be converted back
    controls = {int(a): b for a, b in keys.items()}
    if version >= 2:
        infinite_soft_drop = controls_config["infinite_soft_drop"]
        infinite_hold = controls_config["infinite_hold"]
    # convert escape codes to key names
    if version < 3:
        for control, s in controls.items():
            if s in ui.ASCII_TO_NAME:
                controls[control] = ui.ASCII_TO_NAME[s]
            elif s in ui.ESCAPE_CODE_TO_NAME:
                controls[control] = ui.ESCAPE_CODE_TO_NAME[s]
else:
    controls = default_controls.copy()

controls_config = {
    "version": 3,
    "keys": controls,
    "infinite_soft_drop": infinite_soft_drop,
    "infinite_hold": infinite_hold
}

try:
    main_ui.init()
    playing = True
    while playing:
        option = main_ui.menu(("Play", "Objective", "Controls", "Bag Type", "Infinite Soft Drop", "Infinite Hold", "UI Options", "Quit"))
        if option == 0:
            randomiser: game.Randomiser
            if bag_type == 0:
                randomiser = game.BagRandomiser(1, 0)
            elif bag_type == 1:
                randomiser = game.BagRandomiser(2, 0)
            elif bag_type == 2:
                randomiser = game.BagRandomiser(1, 1)
            elif bag_type == 3:
                randomiser = game.BagRandomiser(1, 2)
            else:
                randomiser = game.ClassicRandomiser()
            if objective == 0:
                objective_type = game.OBJECTIVE_NONE
                objective_count = 0
            elif objective == 1:
                objective_type = game.OBJECTIVE_LINES
                objective_count = 20
            elif objective == 2:
                objective_type = game.OBJECTIVE_LINES
                objective_count = 40
            elif objective == 3:
                objective_type = game.OBJECTIVE_LINES
                objective_count = 100
            elif objective == 4:
                objective_type = game.OBJECTIVE_TIME
                objective_count = 60
            elif objective == 5:
                objective_type = game.OBJECTIVE_TIME
                objective_count = 120
            main_ui.main_loop(game.Game(objective_type, objective_count, randomiser, controls, infinite_soft_drop, infinite_hold), tps=game.TPS)
        elif option == 1:
            objective = main_ui.menu(("None", "20 lines", "40 lines", "100 lines", "1 minute", "2 minutes"), starting_option=objective)
        elif option == 2:
            option = 0
            while True:
                options = ("Close", "Defaults") + tuple((x, controls[i]) for i, x in enumerate(CONTROL_NAMES))
                option = main_ui.menu(options, starting_option=option)
                if option == 0:
                    break
                elif option == 1:
                    controls = default_controls.copy()
                    continue
                else:
                    key = option - 2
                main_ui.draw_text(f"Press key for {CONTROL_NAMES[key].lower()}", main_ui.width // 2, main_ui.height // 10, align=ui.ALIGN_CENTER)
                main_ui.update_screen()
                controls[key] = main_ui.get_key()
            controls_config["keys"] = controls
            config.save("controls", controls_config)
        elif option == 3:
            bag_type = main_ui.menu(("7 Bag", "14 Bag", "7+1 Bag", "7+2 Bag", "Classic"), starting_option=bag_type)
        elif option == 4:
            infinite_soft_drop = main_ui.menu(("Enable", "Disable")) == 0
            controls_config["infinite_soft_drop"] = infinite_soft_drop
            config.save("controls", controls_config)
        elif option == 5:
            infinite_hold = main_ui.menu(("Enable", "Disable")) == 0
            controls_config["infinite_hold"] = infinite_hold
            config.save("controls", controls_config)
        elif option == 6:
            main_ui.options_menu()
        else:
            playing = False
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
