import time, logging

# file imports #
from variables import Variables
from config import Config

from utils.input.mouse import left_click, move_mouse
import utils.input.keyboard as Keyboard

from utils.images.screen import screen_region

class SellUI:
    def __init__(self):
        self.total_sold = 0
    
    def toggle_shop(self):
        Keyboard.press_key("g")
        time.sleep(1)

    def sell_items(self, total_sold_add):
        if Variables.is_paused:                 logging.debug("Paused, skipping..."); return
        if not Variables.is_idle():             logging.debug("Not idle, skipping..."); return
        if not Variables.is_roblox_focused:     logging.debug("Roblox is not focused."); return
        Variables.is_selling = True

        # sell items #
        move_mouse(screen_region["width"] // 2, screen_region["height"] // 2)

        self.toggle_shop()
        time.sleep(0.5)

        move_mouse(*Config.AUTO_SELL_BUTTON_POSITION)
        time.sleep(0.35)
        left_click()
        time.sleep(0.5)
        self.toggle_shop()

        self.total_sold = total_sold_add
        Variables.is_selling = False
