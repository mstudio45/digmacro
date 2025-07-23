import os, time, threading, logging
import numpy as np
import cv2

# file imports #
from variables import Variables, StaticVariables
from config import Config

from utils.images.screenshots import take_screenshot
from utils.input.mouse import clicking_lock, left_click_lock

from utils.images.screen import scale_x_1080p, scale_y_1080p, scale_factor, write_image, stack_images_with_dividers

from utils.detectors.playerbar import PlayerBar
from utils.detectors.dirtbar import DirtBar

## MAIN HANDLER FOR CLICKS ##
class MainHandler:
    def __init__(self):
        self.current_fps = 0.0

        # initliaze classes #
        self.PlayerBar = PlayerBar()
        self.DirtBar = DirtBar()

        # variables #
        self.minigame_detected_by_avg = False

        self.click_cooldown = 0
        self.debug_img = None
        self.resized_image_size = (1, 1)

        # cache to class for faster get #
        self.region_left, self.region_top, _, _ = Variables.minigame_region.values()
        self.use_prediction = Config.USE_PREDICTION
        self.computer_vision = Config.SHOW_COMPUTER_VISION

        # buffers #
        self._gray_buffer = None
        self._resize_buffer = None
        
    def setup_region_image_size(self):
        if Variables.minigame_region is None: return
        
        # config #
        self.use_prediction = Config.USE_PREDICTION
        self.computer_vision = Config.SHOW_COMPUTER_VISION

        # resize image #
        region = Variables.minigame_region

        self.region_left, self.region_top, region_width, region_height = region.values()
        self.resized_image_size = (int(region_width * scale_x_1080p), int(region_height * scale_y_1080p))

        logging.info(f"Region Image size: ({region_width}, {region_height}) -> {self.resized_image_size}")

        # only reallocate if buffer is None or shape changed #
        if scale_factor > 1:
            resize_shape = (int(region_height * scale_y_1080p), int(region_width * scale_x_1080p), 4)
            gray_shape = (int(region_height * scale_y_1080p), int(region_width * scale_x_1080p))

            if self._resize_buffer is None:
                self._resize_buffer = np.empty(resize_shape, dtype=np.uint8)

            elif self._resize_buffer.shape != resize_shape:
                del self._resize_buffer
                self._resize_buffer = np.empty(resize_shape, dtype=np.uint8)
            
            if self._gray_buffer is None:
                self._gray_buffer = np.empty(gray_shape, dtype=np.uint8)
            elif self._gray_buffer.shape != gray_shape:
                del self._gray_buffer
                self._gray_buffer = np.empty(gray_shape, dtype=np.uint8)
        else:
            gray_shape = (region_height, region_width)
            
            if self._gray_buffer is None:
                self._gray_buffer = np.empty(gray_shape, dtype=np.uint8)
                
            elif self._gray_buffer.shape != gray_shape:
                del self._gray_buffer
                self._gray_buffer = np.empty(gray_shape, dtype=np.uint8)

        logging.info("Empty buffers created successfully.")

    def update_state(self, sct):
        vars = Variables
        if vars.is_selecting_region == False:
            if vars.is_paused == True or (vars.is_roblox_focused == False or vars.is_rejoining == True) or vars.is_selling == True:        
                del vars; return
        
        # take screenshots #
        screenshot_np = take_screenshot(vars.minigame_region, sct)
        if screenshot_np is None:
            vars.is_minigame_active = False
            del vars; return
        
        # resize image to 1080p and change to gray_scale #
        if scale_factor > 1:
            cv2.resize(screenshot_np, self.resized_image_size, dst=self._resize_buffer, interpolation=cv2.INTER_AREA)
            screenshot_np = self._resize_buffer
        
        cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2GRAY, dst=self._gray_buffer)
        gray_screenshot = self._gray_buffer
        if gray_screenshot is None:
            vars.is_minigame_active = False
            del vars; return

        # selection region #
        if vars.is_selecting_region == True:        
            self.DirtBar.find_dirt(gray_screenshot,  self.region_left, self.region_top)
            self.PlayerBar.find_bar(gray_screenshot, self.region_left, self.DirtBar.clickable_position)
            self.create_debug_image(screenshot_np)
            del vars; return
        
        # check the minigame #
        left_diff = np.ptp( np.mean(screenshot_np[:, :15, :3], axis=(0, 1)) )
        if left_diff > 1:
            right_diff = np.ptp( np.mean(screenshot_np[:, -15:, :3], axis=(0, 1)) )
            if right_diff > 1:
                vars.is_minigame_active = False
                del vars; return

        # find all stuff #
        self.DirtBar.find_dirt(gray_screenshot,  self.region_left, self.region_top)
        self.PlayerBar.find_bar(gray_screenshot, self.region_left, self.DirtBar.clickable_position)
        
        if self.PlayerBar.current_position is None:
            vars.is_minigame_active = False
            del vars; return
        
        # enable the minigame #
        vars.is_minigame_active = True
        if self.computer_vision: self.create_debug_image(screenshot_np) # debug_img will be overwritten #

        ############### cleanup ###############
        del vars
        return True

    def handle_click(self):
        if not Variables.is_minigame_active: return

        vars = Variables
        current_time_ms = int(time.time() * 1000)

        vars.last_minigame_detection = current_time_ms
        # if current_time_ms < self.click_cooldown or clicking_lock.locked():
        #     del vars; return # early exit, we are on a cooldown #

        # positions #
        # player_bar = self.PlayerBar
        # 
        # player_bar_center = player_bar.current_position
        # clickable_part = self.DirtBar.clickable_position
        # 
        # clickable_width = clickable_part[2]
        # clickable_center = clickable_part[0] + (clickable_width // 2)
        # clickable_radius = clickable_width // 2

        # prediction variables #
        # confidence = 0.0
        # should_click = False
        # prediction_used = False
        # click_delay = 0

        # verify if we should click or no #
        # if player_bar.bar_in_clickable:
        #     should_click = True
        # 
        # elif self.use_prediction:
        #     predicted_player_bar = player_bar.predicted_position
        #     current_velocity = player_bar.current_velocity
        # 
        #     if predicted_player_bar is not None and abs(current_velocity) >= Config.PREDICTION_MIN_VELOCITY: # check required velocity #
        #         player_bar_to_clickable = (player_bar_center < clickable_center) if current_velocity > 0 else (player_bar_center > clickable_center)
        # 
        #         if player_bar_to_clickable: # check if player bar is going towards clickable part #
        #             distance_to_center_PREDICTED = abs(predicted_player_bar - clickable_center)
        # 
        #             if distance_to_center_PREDICTED <= clickable_radius: # check if prediction bar is inside the clickable part #
        #                 confidence = 1.0 - (distance_to_center_PREDICTED / clickable_radius)
        # 
        #                 if confidence >= Config.PREDICTION_CONFIDENCE:
        #                     distance_to_player_bar_CLICKABLE = clickable_center - player_bar_center
        #                     arrival_in_ms = distance_to_player_bar_CLICKABLE / current_velocity
        # 
        #                     if arrival_in_ms > 0 and arrival_in_ms <= Config.PREDICTION_MAX_TIME_AHEAD: # check if arrival time is under the max time ahead #
        #                         should_click, prediction_used, click_delay = True, True, arrival_in_ms
        
        # do the click #
        # if should_click:
        if self.PlayerBar.bar_in_clickable:
            clicking_lock.acquire()
            threading.Thread(target=left_click_lock, args=(0,)).start()

            self.click_cooldown = current_time_ms + Config.MIN_CLICK_INTERVAL # + click_delay
            vars.click_count += 1

            # screenshot handler #
            def screenshot():
                if Config.SCREENSHOT_EVERY_CLICK:
                    write_image(os.path.join(StaticVariables.prediction_screenshots_path, f"{vars.click_count}.png"), self.debug_img) # "_found" if prediction_used else ""

                # if prediction_used and Config.PREDICTION_SCREENSHOTS:
                #     time.sleep(click_delay)
                #     write_image(os.path.join(StaticVariables.prediction_screenshots_path, f"{vars.click_count}_pred_clicked.png"), self.debug_img)
            
            threading.Thread(target=screenshot, daemon=True).start()
        
        ############### cleanup ###############
        del vars

    def create_debug_image(self, screenshot_np):
        screenshot_height = screenshot_np.shape[0]

        player_bar, dirt_bar = self.PlayerBar, self.DirtBar
        region_left = self.region_left
        
        # draw the dirt part and clickable part #
        if dirt_bar.position:
            dx, _, dw, _ = dirt_bar.position
            cv2.rectangle(screenshot_np, (dx - region_left, 0), (dx - region_left + dw, screenshot_height), (0, 255, 255), 2)
        
        if dirt_bar.clickable_position:
            cx, _, cw, _ = dirt_bar.clickable_position
            cv2.rectangle(screenshot_np, (cx - region_left, 0), (cx - region_left + cw, screenshot_height), (125, 255, 0), 2)

        # draw the player bar (current and prediction) #
        plr_x = player_bar.current_position
        pred_x = player_bar.predicted_position
        plr_w = Config.PLAYER_BAR_WIDTH

        if plr_x is not None:
            plr_x = int(plr_x - region_left)
            cv2.line(screenshot_np, (plr_x, 0), (plr_x, screenshot_height), (0, 0, 255), plr_w)

        if pred_x is not None:
            pred_x = int(pred_x - region_left)
            cv2.line(screenshot_np, (pred_x, 0), (pred_x, screenshot_height), (255, 0, 255), plr_w) 

        # finally set the debug img #
        if Config.SHOW_DEBUG_MASKS:
            self.debug_img = stack_images_with_dividers([ screenshot_np, player_bar.mask, dirt_bar.mask ])
        else:
            self.debug_img = screenshot_np