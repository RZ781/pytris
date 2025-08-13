# pytris
A modern TUI and GUI multiplayer stacker game implemented in Python.

## Dependencies
Python 3.7 or later is required.
I primarily test with Python 3.11, so if anything doesn't on an earlier version, create an issue or a pull request.
To play the GUI version, pygame is also required.

## Starting from a terminal
Run `python3 pytris` to start the terminal version, or `python3 pytris --pygame` to start the GUI version.
If the GUI version opens when you use `python3 pytris`, use `python3 pytris --terminal` instead.
To connect to a remote server, add `--address=<server address>`, and to start a server run `python3 pytris --server`.
If you are on Windows you may need to replace `python3` with `py`.

## Starting outside terminal
Run `install.py` to generate a `Pytris Terminal` and `Pytris GUI` shortcut file.
Alternatively, you can manually create a shell script, shortcut, or desktop file to start it with any arguments you want.
If you use a method to start pytris which doesn't give it a terminal, e.g. a shortcut using `pythonw.exe` on Windows or a desktop file with `Terminal=false`, the GUI version will attempt to run unless otherwise specified using `--terminal`.
