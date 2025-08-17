# pytris
A modern TUI and GUI multiplayer stacker game implemented in Python.

## Dependencies
- Python `3.7+`
- Pygame `2.6.1+` (optional; for GUI)

I primarily test with Python 3.11, so if anything doesn't work on an earlier version, create an issue or a pull request.

## Starting from a terminal
To run the terminal (TUI) version, start with:
```
$ python3 pytris
```
To run the graphical version, start with:
```
$ python3 pytris --pygame
```

> **Note** <br>
> The GUI version may open when you use `python3 pytris`. If this happens, use `python3 pytris --terminal` instead.

> **Note** <br>
> Windows users may need to use `py` instead of `python3`.

### Multiplayer
To start a server, use:
```
$ python3 pytris --server
```

Clients can connect with by adding the argument `--address=` following with the appropriate server address

## Starting outside the terminal
You can generate two shortcut files, `Pytris Terminal` and `Pytris GUI` using the `install.py` script with:
```
$ python3 install.py
```
Move these to `%ProgramData%\Microsoft\Windows\Start Menu\Programs` (on Windows) to be able to launch Pytris from the start menu.

Alternatively, manually create a shell script, shortcut, or desktop file to start it with any arguments you want (or edit the generated files).

> **Note** <br>
> If you use a method to start pytris which doesn't give it a terminal, e.g. a shortcut using `pythonw.exe` on Windows or a desktop file with `Terminal=false`, the GUI version will attempt to run unless otherwise specified using `--terminal`.
