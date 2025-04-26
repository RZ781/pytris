import os, json
from typing import Any

pytris_folder = os.path.expanduser("~/.pytris")

def load(name: str) -> Any:
    if not os.path.isdir(pytris_folder):
        os.mkdir(pytris_folder)
    path = f"{pytris_folder}/{name}.json"
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)

def save(name: str, data: Any) -> None:
    if not os.path.isdir(pytris_folder):
        os.mkdir(pytris_folder)
    path = f"{pytris_folder}/{name}.json"
    with open(path, "w") as f:
        return json.dump(data, f)
