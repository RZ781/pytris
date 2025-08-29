import os, sys, time, importlib.util
import game, ui, config, multiplayer, menu
from typing import Sequence

config.init()

use_terminal = False
use_pygame = False
server = False
server_port = multiplayer.PYTRIS_PORT
for arg in sys.argv[1:]:
    if arg == "--terminal":
        use_terminal = True
    elif arg == "--pygame":
        use_pygame = True
    elif arg == "--server":
        server = True
    elif arg.startswith("--port="):
        try:
            server_port = int(arg[len("--port="):])
        except ValueError:
            sys.exit("error: invalid port")
    else:
        sys.exit(f"error: invalid argument {arg}")

if use_terminal and use_pygame:
    sys.exit("error: --terminal and --pygame cannot be used together")

if not use_terminal and not use_pygame:
    pygame_installed = importlib.util.find_spec("pygame") is not None
    in_terminal = sys.stdin is not None and sys.stdin.isatty()
    if in_terminal:
        use_terminal = True
    elif pygame_installed and (sys.platform != "linux" or os.environ.get("DISPLAY", "") != "" or os.environ.get("WAYLAND_DISPLAY", "") != ""):
        use_pygame = True
    else:
        sys.exit("error: terminal and pygame are both unavailable (use --terminal or --pygame to force one to run)")

if server:
    multiplayer.server(server_port)
    sys.exit()

main_ui: ui.UI
if use_pygame:
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
    game.Key.PAUSE: "p",
}

controls_config = config.load("controls")
if controls_config and controls_config.get("version", None) == 4:
    infinite_soft_drop = controls_config["infinite_soft_drop"]
    # json casts all keys to strings, so they must be converted back
    keys = controls_config["keys"]
    controls = {game.Key(int(a)): b for a, b in keys.items()}
    # add missing keys
    controls = {**default_controls, **controls}
else:
    controls = default_controls.copy()
    infinite_soft_drop = False

controls_config = {
    "version": 4,
    "keys": {key.value: controls[key] for key in controls},
    "infinite_soft_drop": infinite_soft_drop
}

class PlayButton(menu.Button):
    def __init__(self, name: str, multiplayer: bool = False) -> None:
        self.name = [name]
        self.multiplayer = multiplayer
    def click(self) -> None:
        config = game.GameConfig()
        randomiser: game.Randomiser
        if self.multiplayer:
            randomiser = game.BagRandomiser(1, 0)
            spin_types = [game.SpinType.SPIN, game.SpinType.MINI, game.SpinType.NONE, game.SpinType.NONE]
        else:
            randomiser = (
                game.BagRandomiser(1, 0),
                game.BagRandomiser(2, 0),
                game.BagRandomiser(1, 1),
                game.BagRandomiser(1, 2),
                game.ClassicRandomiser()
            )[bag_type_menu.current]
            config.objective_type = (
                game.Objective.NONE,
                game.Objective.LINES,
                game.Objective.LINES,
                game.Objective.LINES,
                game.Objective.TIME,
                game.Objective.TIME
            )[objective_menu.current]
            config.objective_count = (0, 20, 40, 100, 60, 120)[objective_menu.current]
            config.width = (10, 4, 5, 20)[board_size_menu.current]
            config.height = (20, 24, 10, 20)[board_size_menu.current]
            config.garbage_type = game.GarbageType(garbage_menu.current)
            config.garbage_cancelling = garbage_cancelling_menu.current == 0
            config.hold_type = game.HoldType(hold_menu.current)
            config.lock_delay = lock_delay_selector.value
            spin_types = [game.SpinType(m.current) for m in spin_menus]
        config.infinite_soft_drop = soft_drop_menu.current == 0
        x = game.Game(config, randomiser, controls)
        x.set_spins(*spin_types)
        if self.multiplayer:
            server_ip = server_ip_input.value
            if not server_ip:
                server_ip = "127.0.0.1"
            server_port = server_port_input.value
            if not server_port:
                server_port = str(multiplayer.PYTRIS_PORT)
            connection = multiplayer.connect_to_server(server_ip, server_port)
            if connection is None:
                self.menu.set_info_text("No server found")
                self.menu.resize(self.ui.width, self.ui.height)
                return
            x.set_connection(connection)
        self.ui.push_menu(x)

class SoftDropSelection(menu.Button):
    def __init__(self, name: str) -> None:
        self.name = [name]
    def click(self) -> None:
        self.ui.pop_menu()
        controls_config["infinite_soft_drop"] = soft_drop_menu.current == 0
        config.save("controls", controls_config)

class ControlMenu(ui.Menu):
    def __init__(self, name: str, key: game.Key) -> None:
        self.name = name
        self.control = key
    def enable_custom_handling(self) -> bool:
        return False
    def init(self, ui: ui.UI) -> None:
        self.ui = ui
    def resize(self, width: int, height: int) -> None:
        self.ui.draw_text(f"Press key for {self.name.lower()}", self.ui.width // 2, self.ui.height // 10, align=ui.Alignment.CENTER)
        self.ui.update_screen()
    def key(self, c: str, repeated: bool = False) -> None:
        if repeated:
            return
        controls[self.control] = c
        self.ui.pop_menu()
    def tick(self) -> None:
        pass

class ControlButton(menu.Button):
    def __init__(self, name: str, key: game.Key) -> None:
        self.control_name = name
        self.key = key
        self.control_menu = ControlMenu(name, key)
    def get_name(self) -> Sequence[str]:
        return [self.control_name, controls[self.key]]
    def click(self) -> None:
        self.ui.push_menu(self.control_menu)

class ControlsCloseButton(menu.Button):
    def __init__(self) -> None:
        self.name = ["Close"]
    def click(self) -> None:
        controls_config["keys"] = {key.value: controls[key] for key in controls}
        config.save("controls", controls_config)
        self.ui.pop_menu()

class PresetButton(menu.Button):
    def __init__(self,
                 name: str,
                 objective: int = 0,
                 bag_type: int = 0,
                 board_size: int = 0,
                 spin_types: Sequence[int] = [2, 1, 0, 0],
                 garbage_type: int = 0,
                 hold_type: int = 1,
                 garbage_cancelling: bool = True,
                 lock_delay: int = 30):
        self.name = [name]
        self.objective = objective
        self.bag_type = bag_type
        self.board_size = board_size
        self.spin_types = spin_types
        self.garbage_type = garbage_type
        self.hold_type = hold_type
        self.garbage_cancelling = garbage_cancelling
        self.lock_delay = lock_delay
    def click(self) -> None:
        self.ui.pop_menu()
        objective_menu.current = self.objective
        bag_type_menu.current = self.bag_type
        board_size_menu.current = self.board_size
        for i, m in enumerate(spin_menus):
            m.current = self.spin_types[i]
        garbage_menu.current = self.garbage_type
        hold_menu.current = self.hold_type
        garbage_cancelling_menu.current = 0 if self.garbage_cancelling else 1
        lock_delay_selector.value = self.lock_delay

controls_menu = menu.Menu([
    ControlsCloseButton(),
    ControlButton("Left", game.Key.LEFT),
    ControlButton("Right", game.Key.RIGHT),
    ControlButton("Soft Drop", game.Key.SOFT_DROP),
    ControlButton("Hard Drop", game.Key.HARD_DROP),
    ControlButton("Rotate", game.Key.ROTATE),
    ControlButton("Rotate Clockwise", game.Key.CLOCKWISE),
    ControlButton("Rotate Anticlockwise", game.Key.ANTICLOCKWISE),
    ControlButton("Rotate 180", game.Key.ROTATE_180),
    ControlButton("Hold", game.Key.HOLD),
    ControlButton("Forfeit", game.Key.FORFEIT),
    ControlButton("Pause", game.Key.PAUSE)
])

preset_menu = menu.Menu([
    PresetButton("Marathon"),
    PresetButton("Classic", bag_type=4, spin_types=[0, 0, 0, 0], hold_type=0, lock_delay=1),
    PresetButton("40 Lines", objective=2),
    PresetButton("Ultra", objective=5),
    PresetButton("Survival", garbage_type=2, garbage_cancelling=False),
    PresetButton("Big Mode", board_size=2, spin_types=[2, 1, 0, 1]),
    PresetButton("4 Wide", board_size=1, spin_types=[2, 1, 0, 1]),
    PresetButton("Chaos", objective=5, bag_type=1, spin_types=[2, 2, 2, 2], garbage_type=6, hold_type=0, garbage_cancelling=False),
])

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
    SoftDropSelection("Enable"),
    SoftDropSelection("Disable")
], 0 if infinite_soft_drop else 1)

hold_menu = menu.Menu([
    menu.Selection("No Hold"),
    menu.Selection("Normal"),
    menu.Selection("Infinite Hold")
], 1)

board_size_menu = menu.Menu([
    menu.Selection("Normal"),
    menu.Selection("4 Wide"),
    menu.Selection("Big Mode"),
    menu.Selection("Massive (20x20)")
])

garbage_menu = menu.Menu([
    menu.Selection("None"),
    menu.Selection("Slow Cheese"),
    menu.Selection("Fast Cheese"),
    menu.Selection("Slow Clean"),
    menu.Selection("Fast Clean"),
    menu.Selection("Backfire"),
    menu.Selection("Delayed Backfire")
])

garbage_cancelling_menu = menu.Menu([
    menu.Selection("Enable"),
    menu.Selection("Disable")
])

spin_names = ("T Spin", "Mini T Spin", "Immobile T Piece", "Immobile Piece")
spin_menus = [menu.Menu([menu.Selection("None"), menu.Selection("Mini Spin"), menu.Selection("Full Spin")], default) for default in (2, 1, 0, 0)]

spin_type_menu = menu.Menu([menu.Selection("Close")] + [
    menu.PreviewSubmenu(name, m) for name, m in zip(spin_names, spin_menus)
])

lock_delay_selector = menu.NumberSelector("Lock Delay", 30, 0, 60, "{} frames")

server_ip_input = menu.TextInput("Server IP", "Type in server IP address")
server_port_input = menu.TextInput("Server Port", "Type in server IP address")

main_menu = menu.Menu([
    PlayButton("Play"),
    PlayButton("Multiplayer", multiplayer=True),
    server_ip_input,
    server_port_input,
    menu.Submenu("Controls", controls_menu),
    menu.Submenu("Presets", preset_menu),
    menu.PreviewSubmenu("Objectives", objective_menu),
    menu.PreviewSubmenu("Bag Type", bag_type_menu),
    menu.PreviewSubmenu("Infinite Soft Drop", soft_drop_menu),
    menu.PreviewSubmenu("Hold", hold_menu),
    menu.PreviewSubmenu("Board Size", board_size_menu),
    menu.PreviewSubmenu("Garbage", garbage_menu),
    menu.PreviewSubmenu("Garbage Cancelling", garbage_cancelling_menu),
    menu.Submenu("Spin Detection", spin_type_menu),
    lock_delay_selector,
    menu.Submenu("UI Options", main_ui.get_options_menu()),
    menu.Selection("Quit")
])

try:
    main_ui.init()
    main_ui.push_menu(main_menu)
    main_ui.main_loop()
except KeyboardInterrupt: # ctrl-c
    pass
finally:
    main_ui.quit()
