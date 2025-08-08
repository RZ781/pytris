import os, json, sys
from typing import Any

if sys.platform == "win32":
    pytris_folder = os.path.expanduser("~/.pytris")
else:
    pytris_folder = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")) + "/pytris"

def init() -> None:
    if not os.path.isdir(pytris_folder):
        os.makedirs(pytris_folder)

def load(name: str) -> Any:
    if not os.path.isdir(pytris_folder):
        os.mkdir(pytris_folder)
    path = f"{pytris_folder}/{name}.json"
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

def save(name: str, data: Any) -> None:
    if not os.path.isdir(pytris_folder):
        os.mkdir(pytris_folder)
    path = f"{pytris_folder}/{name}.json"
    with open(path, "w") as f:
        return json.dump(data, f)
