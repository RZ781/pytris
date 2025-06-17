#!/usr/bin/env python3
import sys, time
import game, ui, config, multiplayer

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

bag_type = 0
objective = 0
garbage_type = 0
garbage_cancelling = True
infinite_soft_drop = False
hold_type = 1
spin_type = 0
size = 0

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

try:
    main_ui.init()
    playing = True
    option = 0
    while playing:
        option = main_ui.menu(("Play", "Multiplayer", "Presets", "Objective", "Controls", "Bag Type", "Infinite Soft Drop", "Hold", "Board Size", "Spin Detection", "Garbage", "Garbage Cancelling", "UI Options", "Quit"), starting_option=option)
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
                objective_type = game.Objective.NONE
                objective_count = 0
            elif objective == 1:
                objective_type = game.Objective.LINES
                objective_count = 20
            elif objective == 2:
                objective_type = game.Objective.LINES
                objective_count = 40
            elif objective == 3:
                objective_type = game.Objective.LINES
                objective_count = 100
            elif objective == 4:
                objective_type = game.Objective.TIME
                objective_count = 60
            else:
                objective_type = game.Objective.TIME
                objective_count = 120
            if size == 0:
                board_width = 10
                board_height = 20
            elif size == 1:
                board_width = 4
                board_height = 24
            elif size == 2:
                board_width = 5
                board_height = 10
            else:
                board_width = 20
                board_height = 20
            x = game.Game(randomiser, board_width, board_height, game.SpinType(spin_type), game.GarbageType(garbage_type), garbage_cancelling, None)
            x.set_objective(objective_type, objective_count)
            x.set_controls(controls, infinite_soft_drop, game.HoldType(hold_type))
            main_ui.main_loop(x, tps=game.TPS)
        elif option == 1:
            connection = multiplayer.connect_to_server()
            if connection is None:
                main_ui.clear()
                main_ui.draw_text("No server found", main_ui.width//2, main_ui.height//5, align=ui.Alignment.CENTER)
                main_ui.update_screen()
                time.sleep(3)
                continue
            randomiser = game.BagRandomiser(1, 0)
            x = game.Game(randomiser, 10, 20, game.SpinType.ALL_MINI, game.GarbageType.NONE, True, connection)
            x.set_objective(game.Objective.NONE, 0)
            x.set_controls(controls, infinite_soft_drop, game.HoldType.NORMAL)
            main_ui.main_loop(x, tps=game.TPS)
        elif option == 2:
            preset = main_ui.menu(("Marathon", "Classic", "40 Lines", "Ultra", "Survival", "Big Mode", "4 Wide", "Chaos"))
            objective    = (0, 0, 2, 5, 0, 0, 0, 5)[preset]
            bag_type     = (0, 4, 0, 0, 0, 0, 0, 1)[preset]
            size         = (0, 0, 0, 0, 0, 2, 1, 0)[preset]
            spin_type    = (0, 3, 0, 0, 0, 2, 2, 1)[preset]
            garbage_type = (0, 0, 0, 0, 2, 0, 0, 5)[preset]
            hold_type    = (1, 0, 1, 1, 1, 1, 1, 0)[preset]
            garbage_cancelling = bool((1, 1, 1, 1, 0, 1, 1, 0)[preset])
        elif option == 3:
            objective = main_ui.menu(("None", "20 lines", "40 lines", "100 lines", "1 minute", "2 minutes"), starting_option=objective)
        elif option == 4:
            choice = 0
            while True:
                options = ("Close", "Defaults") + tuple((CONTROL_NAMES[key.value], controls[key]) for key in game.Key)
                choice = main_ui.menu(options, starting_option=choice)
                if choice == 0:
                    break
                elif choice == 1:
                    controls = default_controls.copy()
                    continue
                else:
                    key = game.Key(choice - 2)
                main_ui.draw_text(f"Press key for {CONTROL_NAMES[key.value].lower()}", main_ui.width // 2, main_ui.height // 10, align=ui.Alignment.CENTER)
                main_ui.update_screen()
                controls[key] = main_ui.get_key()
            controls_config["keys"] = {key.value: controls[key] for key in controls}
            config.save("controls", controls_config)
        elif option == 5:
            bag_type = main_ui.menu(("7 Bag", "14 Bag", "7+1 Bag", "7+2 Bag", "Classic"), starting_option=bag_type)
        elif option == 6:
            infinite_soft_drop = main_ui.menu(("Enable", "Disable"), starting_option = 0 if infinite_soft_drop else 1) == 0
            controls_config["infinite_soft_drop"] = infinite_soft_drop
            config.save("controls", controls_config)
        elif option == 7:
            hold_type = main_ui.menu(("No Hold", "Normal", "Infinite Hold"), starting_option=hold_type)
        elif option == 8:
            size = main_ui.menu(("Normal", "4 Wide", "Big Mode", "Massive (20x20)"), starting_option=size)
        elif option == 9:
            spin_type = main_ui.menu(("T Spin", "All Spin", "All Mini", "None"), starting_option=spin_type)
        elif option == 10:
            garbage_type = main_ui.menu(("None", "Slow Cheese", "Fast Cheese", "Slow Clean", "Fast Clean", "Backfire"), starting_option=garbage_type)
        elif option == 11:
            garbage_cancelling = main_ui.menu(("Enable", "Disable"), 0 if garbage_cancelling else 1) == 0
        elif option == 12:
            main_ui.options_menu()
        else:
            playing = False
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
