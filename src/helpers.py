import os
import time
import platform


def splash():
    """ Displays splash screen """
    print("""
███████ ███████ ██████   ██████  ████████ ██ ███████ ██    ██
   ███  ██      ██   ██ ██    ██    ██    ██ ██       ██  ██
  ███   ███████ ██████  ██    ██    ██    ██ █████     ████
 ███         ██ ██      ██    ██    ██    ██ ██         ██
███████ ███████ ██       ██████     ██    ██ ██         ██
    """)


def clear_console():
    """ Clear the console window """
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def wait(seconds: int = 3):
    """ Pause for a set number of seconds """
    for i in range(seconds)[::-1]:
        print(f"\rWait for {i + 1} second(s)...")
        time.sleep(1)


def sanitize_data(value):
    """ Returns given string with problematic removed """
    sanitize = ["\\", "/", ":", "*", "?", "'", "<", ">", '"']
    for i in sanitize:
        value = value.replace(i, "")
    return value.replace("|", "-")


def split_input(selection):
    """ Returns a list of inputted strings """
    if "-" in selection:
        return list(range(int(selection.split('-')[0]), int(selection.split('-')[1] + 1)))
    return list(selection.strip().split(' '))

