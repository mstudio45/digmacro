import os
import time
import threading
import logging

import numpy as np
import cv2

# file imports #
from variables import Variables, StaticVariables
from config import Config

from utils.images.screenshots import take_screenshot
from utils.input.mouse import clicking_lock, left_click_lock

from utils.images.screen import scale_x_1080p, scale_y_1080p, scale_factor, write_image, stack_images_with_dividers

from utils.detectors.minigame.opencv.playerbar import PlayerBar
from utils.detectors.minigame.opencv.dirtbar import DirtBar

## MAIN HANDLER FOR CLICKS ##
class DebugColors:
    DIRT_BOX = (0, 255, 255)       # Cyan #
    CLICKABLE_BOX = (125, 255, 0)  # Green #
    PLAYER_BAR = (0, 0, 255)       # Red #
    PREDICTED_BAR = (255, 0, 255)  # Magenta #

class MainHandler:
    def __init__(self):
        self.current_fps = 0.0

        # initliaze classes #
        self.PlayerBar = PlayerBar()
        self.DirtBar = DirtBar()

        # variables #
        self.click_cooldown = 0
        self.debug_img = None
        self.resized_image_size = (1, 1)

        # cache to class for faster get #
        self.region_left, self.region_top, _, _ = Variables.minigame_region.values()
        self.enable_prediction = Config.ENABLE_PREDICTION
        self.computer_vision = Config.SHOW_COMPUTER_VISION
        self.show_debug_masks = Config.SHOW_DEBUG_MASKS
        self.playerbar_width = Config.PLAYER_BAR_WIDTH
        
        # buffers #
        self._gray_buffer = None
        self._resize_buffer = None
        
    def setup_region_image_size(self):
        if Variables.minigame_region is None: return
        
        # config #
        self.enable_prediction = Config.ENABLE_PREDICTION
        self.computer_vision = Config.SHOW_COMPUTER_VISION
        self.show_debug_masks = Config.SHOW_DEBUG_MASKS
        self.playerbar_width = Config.PLAYER_BAR_WIDTH
        self.click_delay_config = Config.MIN_CLICK_INTERVAL

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

    # screenshots #
    def get_screenshots(self, sct):
        screenshot_np = take_screenshot(Variables.minigame_region, sct)
        if screenshot_np is None: return None, None
        
        # resize image to 1080p #
        if scale_factor > 1:
            cv2.resize(screenshot_np, self.resized_image_size, dst=self._resize_buffer, interpolation=cv2.INTER_AREA)
            screenshot_np = self._resize_buffer
        
        # change to gray_scale #
        cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2GRAY, dst=self._gray_buffer)
        gray_screenshot = self._gray_buffer
        if gray_screenshot is None: return None, None

        return screenshot_np, gray_screenshot

    def create_debug_image(self, screenshot_np):
        debug_image = screenshot_np.copy()
        height, _, _ = debug_image.shape
        region_left = self.region_left

        # draw the dirt part and clickable part #
        if self.DirtBar.position:
            x, _, w, _ = self.DirtBar.position
            pt1 = (x - region_left, 0)
            pt2 = (x - region_left + w, height)
            cv2.rectangle(debug_image, pt1, pt2, DebugColors.DIRT_BOX, 2)

        if self.DirtBar.clickable_position:
            x, _, w, _ = self.DirtBar.clickable_position
            pt1 = (x - region_left, 0)
            pt2 = (x - region_left + w, height)
            cv2.rectangle(debug_image, pt1, pt2, DebugColors.CLICKABLE_BOX, 2)

        # draw the player bar (current and prediction) #
        if self.PlayerBar.current_position is not None:
            x_pos = int(self.PlayerBar.current_position - region_left)
            cv2.line(debug_image, (x_pos, 0), (x_pos, height), DebugColors.PLAYER_BAR, self.playerbar_width)

        # if self.PlayerBar.predicted_position is not None:
        #     x_pos = int(self.PlayerBar.predicted_position - region_left)
        #     cv2.line(debug_image, (x_pos, 0), (x_pos, height), DebugColors.PREDICTED_BAR, self.playerbar_width)

        # finally set the debug img #
        if self.show_debug_masks:
            self.debug_img = stack_images_with_dividers([debug_image, self.PlayerBar.mask, self.DirtBar.mask])
        else:
            self.debug_img = debug_image

    # click state #
    def update_state(self, sct):
        if Variables.is_selecting_region == True:
            screenshot_np, gray_screenshot = self.get_screenshots(sct)
            if screenshot_np is None or gray_screenshot is None: return

            self.DirtBar.find_dirt(gray_screenshot,  self.region_left, self.region_top)
            self.PlayerBar.find_bar(gray_screenshot, self.region_left, self.DirtBar.clickable_position)
            self.create_debug_image(screenshot_np)
            return
        
        # handle idle states #
        if Variables.is_paused == True or (Variables.is_roblox_focused == False or Variables.is_rejoining == True) or Variables.is_selling == True: 
            Variables.is_minigame_active = False       
            return
        
        # take screenshots #
        screenshot_np, gray_screenshot = self.get_screenshots(sct)
        if screenshot_np is None or gray_screenshot is None:
            Variables.is_minigame_active = False
            return

        # check the minigame #
        left_diff = np.ptp( np.mean(screenshot_np[:, :15, :3], axis=(0, 1)) )
        if left_diff > 1:
            right_diff = np.ptp( np.mean(screenshot_np[:, -15:, :3], axis=(0, 1)) )
            if right_diff > 1:
                Variables.is_minigame_active = False
                return

        # find all stuff #
        self.DirtBar.find_dirt(gray_screenshot,  self.region_left, self.region_top)
        self.PlayerBar.find_bar(gray_screenshot, self.region_left, self.DirtBar.clickable_position)
        
        if self.PlayerBar.current_position is None:
            Variables.is_minigame_active = False
            return
        
        # enable the minigame #
        Variables.is_minigame_active = True
        if self.computer_vision: self.create_debug_image(screenshot_np)
        return True

    def handle_click(self):
        if not Variables.is_minigame_active: return

        current_time_ms = int(time.time() * 1000)
        Variables.last_minigame_detection = current_time_ms
        
        if current_time_ms < self.click_cooldown or clicking_lock.locked():
            return # early exit, we are on a cooldown #

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
        # elif self.enable_prediction:
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

            self.click_cooldown = current_time_ms + self.click_delay_config # + click_delay
            Variables.click_count += 1

            # screenshot handler #
            def screenshot():
                if Config.SCREENSHOT_EVERY_CLICK:
                    write_image(os.path.join(StaticVariables.prediction_screenshots_folder, f"{Variables.click_count}.png"), self.debug_img) # "_found" if prediction_used else ""

                # if prediction_used and Config.PREDICTION_SCREENSHOTS:
                #     time.sleep(click_delay)
                #     write_image(os.path.join(StaticVariables.prediction_screenshots_folder, f"{vars.click_count}_pred_clicked.png"), self.debug_img)
            
            threading.Thread(target=screenshot, daemon=True).start()