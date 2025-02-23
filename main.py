#!/usr/bin/python3
import sys
import game, ui

main_ui = ui.TerminalUI()

try:
    main_ui.init()
    playing = True
    while playing:
        option = main_ui.menu(("Play", "Quit"))
        if option == 0:
            main_ui.main_loop(game.Game(game.ClassicRandomiser()), tps=game.TPS)
        else:
            playing = False
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
