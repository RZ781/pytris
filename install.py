#!/usr/bin/env python3
import sys, importlib.util, subprocess, os

def ask(prompt):
    while True:
        answer = input(f"{prompt} (Y/N) ").lower().strip()
        if answer == "y":
            return True
        elif answer == "n":
            return False

def install_module(prompt, module):
    installed = importlib.util.find_spec(module) is not None
    if installed:
        return True
    print(prompt)
    install = ask(f"Install {module}?")
    if install:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
        except subprocess.CalledProcessError:
            sys.exit("Your Python installation does not have a functional version of pip. Install pip or use a virtual environment.")
    return install

if not install_module("To generate the shortcuts, pyshortcuts is required.", "pyshortcuts"):
    sys.exit()
import pyshortcuts

pygame_installed = install_module("If you want to play the GUI version, pygame is required.", "pygame")
desktop = ask("Do you want to add shortcuts to your desktop?")
startmenu = ask("Do you want to add shortcuts to your start menu?")

pyshortcuts.make_shortcut(f"{os.getcwd()}/pytris --terminal", name="Pytris Terminal", desktop=desktop, startmenu=startmenu)
if pygame_installed:
    pyshortcuts.make_shortcut(f"{os.getcwd()}/pytris --pygame", name="Pytris GUI", terminal=False, desktop=desktop, startmenu=startmenu)

