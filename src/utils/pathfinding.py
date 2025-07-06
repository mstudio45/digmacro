import time, random

__all__ = ["PathfingingHandler"]

from utils.general.keyboard import press_key, press_multiple_keys
import logging

from config import Config
from variables import Variables

class PathfingingHandler:
    def __init__(self):
        self.current_index = 0

    def get_next_key(self):
        macro = Config.PathfindingMacros[Config.PATHFINDING_MACRO]
        
        was_last_key = False
        if self.current_index > len(macro) - 1:
            was_last_key = True
            self.current_index = 0

        next_key, duration = macro[self.current_index]
        self.current_index = self.current_index + 1

        return next_key, duration, was_last_key
    
    def start_walking(self):
        if not Variables.is_idle(): logging.debug("Not idle, skipping..."); return

        logging.info("Walking started...")
        Variables.is_walking = True

        key, duration, was_last_key = self.get_next_key()
        if isinstance(key, list):
            press_multiple_keys(key, duration)
        else:
            press_key(key, duration)
        
        time.sleep(0.1)
        Variables.is_walking = False
        return was_last_key