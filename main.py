#!/usr/bin/python3
import sys
import game, ui, config

KEYS = {
    "\x1b[A": "Up",
    "\x1b[B": "Down",
    "\x1b[C": "Right",
    "\x1b[D": "Left",
    " ": "Space",
    "\t": "Tab",
    "\n": "Return",
    "\x1b[1~": "Home",
    "\x1b[2~": "Insert",
    "\x1b[3~": "Delete",
    "\x1b[4~": "End",
    "\x1b[5~": "Page Up",
    "\x1b[6~": "Page Down",
    "\x1b": "Escape",
}

CONTROL_NAMES = ("Left", "Right", "Soft Drop", "Hard Drop", "Rotate", "Rotate Clockwise", "Rotate Anticlockwise", "Rotate 180", "Hold")

def key_name(key):
    if key in KEYS:
        return KEYS[key]
    return key

main_ui = ui.TerminalUI()
bag_type = 0
objective = game.OBJECTIVE_NONE

default_controls = {
    game.KEY_LEFT: "\x1b[D",
    game.KEY_RIGHT: "\x1b[C",
    game.KEY_SOFT_DROP: "\x1b[B",
    game.KEY_HARD_DROP: " ",
    game.KEY_ROTATE: "\x1b[A",
    game.KEY_CLOCKWISE: "x",
    game.KEY_ANTICLOCKWISE: "z",
    game.KEY_180: "a",
    game.KEY_HOLD: "c",
}
controls = config.load("controls")
if controls:
    # json casts all keys to strings, so they must be converted back
    controls = {int(a): b for a, b in controls.items()}
else:
    controls = default_controls.copy()
colour_mode = config.load("colours")
if colour_mode:
    mode = colour_mode["mode"]
    modes = main_ui.get_colour_modes()
    if mode in modes:
        main_ui.set_colour_mode(modes.index(mode))

try:
    main_ui.init()
    playing = True
    while playing:
        option = main_ui.menu(("Play", "Objective", "Controls", "Bag Type", "Colours", "Quit"))
        if option == 0:
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
            main_ui.main_loop(game.Game(objective_type, objective_count, randomiser, controls), tps=game.TPS)
        elif option == 1:
            objective = main_ui.menu(("None", "20 lines", "40 lines", "100 lines", "1 minute", "2 minutes"), starting_option=objective)
        elif option == 2:
            option = 0
            while True:
                options = ("Close", "Defaults") + tuple((x, key_name(controls[i])) for i, x in enumerate(CONTROL_NAMES))
                option = main_ui.menu(options, starting_option=option)
                if option == 0:
                    break
                elif option == 1:
                    controls = default_controls.copy()
                    continue
                else:
                    key = option - 2
                text = f"Press key for {CONTROL_NAMES[key].lower()}"
                main_ui.draw_text(text, (main_ui.width - len(text)//2)//2, main_ui.height // 10)
                main_ui.update_screen()
                controls[key] = main_ui.get_key()
            config.save("controls", controls)
        elif option == 3:
            bag_type = main_ui.menu(("7 Bag", "14 Bag", "7+1 Bag", "7+2 Bag", "Classic"), starting_option=bag_type)
        elif option == 4:
            modes = main_ui.get_colour_modes()
            mode = main_ui.menu(modes)
            main_ui.set_colour_mode(mode)
            config.save("colours", {"mode": modes[mode]})
        else:
            playing = False
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
