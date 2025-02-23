#!/usr/bin/python3
import sys
import game, ui

main_ui = ui.TerminalUI()
bag_type = 0

try:
    main_ui.init()
    playing = True
    while playing:
        option = main_ui.menu(("Play", "Bag Type", "Quit"))
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
            main_ui.main_loop(game.Game(randomiser), tps=game.TPS)
        elif option == 1:
            bag_type = main_ui.menu(("7 Bag", "14 Bag", "7+1 Bag", "7+2 Bag", "Classic"))
        else:
            playing = False
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
