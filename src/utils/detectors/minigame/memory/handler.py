import time
import platform
import threading

# file imports #
from variables import Variables
from config import Config

if platform.system() == "Windows":
    from utils.input.mouse import clicking_lock, left_click_lock

    def is_pos_in_bbox(pos_x, left, width):
        return left <= pos_x <= (left + width)

    ## MAIN HANDLER FOR CLICKS ##
    class MainHandler:
        def __init__(self, memory_handler):
            self.memory_handler = memory_handler
            self.dig_gui = None
            self.holder = None
            self.area_strong = None
            self.player_bar = None

            self.current_fps = 0.0
            self.click_cooldown = 0
        
        # update state #
        def update_state(self, sct=None):
            if Variables.is_paused == True or (Variables.is_roblox_focused == False or Variables.is_rejoining == True) or Variables.is_selling == True: 
                Variables.is_minigame_active = False       
                return

            if not self.memory_handler.loaded or not self.memory_handler.playerGui:
                Variables.is_minigame_active = False       
                return
            
            self.dig_gui = self.memory_handler.playerGui.FindFirstChild("Dig")
            if self.dig_gui is None: 
                Variables.is_minigame_active = False       
                return

            self.holder = self.dig_gui.FindFirstChild("Holder", True)
            if self.holder is None:
                Variables.is_minigame_active = False       
                return
            
            self.area_strong = self.holder.FindFirstChild("Area_Strong")
            self.player_bar = self.holder.FindFirstChild("PlayerBar")
            if self.area_strong is None or self.player_bar is None: 
                Variables.is_minigame_active = False       
                return

            Variables.is_minigame_active = True
            return True

        def handle_click(self):
            if not Variables.is_minigame_active: return
            if not self.holder: return

            current_time_ms = int(time.time() * 1000)
            Variables.last_minigame_detection = current_time_ms

            if current_time_ms < self.click_cooldown or clicking_lock.locked():
                return # early exit, we are on a cooldown #

            strong_left = self.area_strong.ScreenPosition[0]
            strong_width = max(20, self.area_strong.Size[0])
            bar_x = self.player_bar.ScreenPosition[0]

            if is_pos_in_bbox(bar_x, strong_left, strong_width):
                clicking_lock.acquire()
                threading.Thread(target=left_click_lock, args=(0,)).start()

                self.click_cooldown = current_time_ms + Config.MIN_CLICK_INTERVAL # + click_delay
                Variables.click_count += 1