#!/usr/bin/python3
import sys
import game, ui, config

main_ui = ui.TerminalUI()
bag_type = 0

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

try:
    main_ui.init()
    playing = True
    while playing:
        option = main_ui.menu(("Play", "Controls", "Bag Type", "Quit"))
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
            main_ui.main_loop(game.Game(randomiser, controls), tps=game.TPS)
        elif option == 1:
            option = 0
            while True:
                options = ("Close", "Defaults", "Left", "Right", "Soft Drop", "Hard Drop", "Rotate", "Rotate Clockwise", "Rotate Anticlockwise", "Rotate 180", "Hold")
                option = main_ui.menu(options, option)
                if option == 0:
                    break
                elif option == 1:
                    controls = default_controls.copy()
                    continue
                elif option == 2:
                    key = game.KEY_LEFT
                elif option == 3:
                    key = game.KEY_RIGHT
                elif option == 4:
                    key = game.KEY_SOFT_DROP
                elif option == 5:
                    key = game.KEY_HARD_DROP
                elif option == 6:
                    key = game.KEY_ROTATE
                elif option == 7:
                    key = game.KEY_CLOCKWISE
                elif option == 8:
                    key = game.KEY_ANTICLOCKWISE
                elif option == 9:
                    key = game.KEY_180
                elif option == 10:
                    key = game.KEY_HOLD
                main_ui.draw_text(f"Press key for {options[option].lower()}", 25, option)
                main_ui.update_screen()
                controls[key] = main_ui.get_key()
            config.save("controls", controls)
        elif option == 2:
            bag_type = main_ui.menu(("7 Bag", "14 Bag", "7+1 Bag", "7+2 Bag", "Classic"), starting_option=bag_type)
        else:
            playing = False
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
