import os, json

pytris_folder = os.path.expanduser("~/.pytris")

def load(name):
    if not os.path.isdir(pytris_folder):
        os.mkdir(pytris_folder)
    path = f"{pytris_folder}/{name}.json"
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)

def save(name, data):
    if not os.path.isdir(pytris_folder):
        os.mkdir(pytris_folder)
    path = f"{pytris_folder}/{name}.json"
    with open(path, "w") as f:
        return json.dump(data, f)
