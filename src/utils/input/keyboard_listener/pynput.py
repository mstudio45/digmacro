import pynput
from typing import Callable

def setup_global_hotkeys(hotkeys: dict[str, Callable]) -> pynput.keyboard.GlobalHotKeys:
    manager = pynput.keyboard.GlobalHotKeys(hotkeys)
    manager.start()
    return manager