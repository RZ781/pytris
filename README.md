# pytris
A modern TUI and GUI multiplayer stacker game implemented in Python.

## Dependencies
Python 3.7 or later is required. I primarily test with Python 3.11, so if anything doesn't on an earlier version, create an issue or a pull request. To play the GUI version, pygame is also required.

## Starting from a terminal
Run `python3 pytris.py` to start the terminal version, or `python3 pytris.py --pygame` to start the GUI version.
If the GUI version opens when you use `python3 pytris.py`, use `python3 pytris.py --terminal` instead.
To connect to a remote server, add `--address=<server address>`, and to start a server run `python3 pytris.py --server`.
If you are on Windows you may need to swap out `python3` for `py`.

## Starting outside terminal
Running `pytris.py` should always run the terminal version.
On Windows, running `pytris.pyw` should run the GUI version.
You can set up a shortcut file on Windows or a .desktop file on Linux to run with the command line options you want.
If whatever method used to start pytris doesn't give it a terminal, e.g. a .pyw file on Windows or a .desktop file with `Terminal=false`, the GUI version will run unless otherwise specified.
