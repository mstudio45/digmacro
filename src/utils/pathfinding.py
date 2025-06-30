import time, random

__all__ = ["PathfingingHandler"]

from utils.general.input import press_key, press_multiple_keys

from config import Config
from variables import Variables

class PathfingingHandler:
    def __init__(self):
        self.current_index = 0

    def get_next_key(self):
        macro = Config.PathfindingMacros[Config.PATHFINDING_MACRO]
        
        if self.current_index > len(macro) - 1: self.current_index = 0
        next_key = macro[self.current_index]
        self.current_index = self.current_index + 1

        return next_key
    
    def start_walking(self):
        if not Variables.is_idle(): print("[PathfingingHandler] Not idle, skipping..."); return

        print("[PathfingingHandler] Walking started...")
        Variables.is_walking = True

        key, duration = self.get_next_key()
        if isinstance(key, list):
            press_multiple_keys(key, duration)
        else:
            press_key(key, duration)
        
        time.sleep(0.1)

        Variables.is_walking = False