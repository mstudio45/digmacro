import os, time, threading, logging, platform
import cv2
import numpy as np

# file imports #
from variables import Variables, StaticVariables
from config import Config

from utils.images.screenshots import take_screenshot
from utils.images.screen import *

import utils.general.mouse as Mouse
import utils.general.keyboard as Keyboard

from utils.general.movement_tracker import MovementTracker

current_os = platform.system()
def is_pos_in_bbox(pos_x, left, width):
    return left <= pos_x <= (left + width)

## SELL ANYWHERE UI ##
class SellUI:
    def __init__(self):
        self.sell_img = resize_image(StaticVariables.sell_anywhere_btn_imgpath)
        self.total_sold = 0
    
    def toggle_shop(self):
        Keyboard.press_key("g")
        time.sleep(1)

    def sell_items(self, total_sold_add):
        if not Variables.is_idle():             logging.debug("Not idle, skipping..."); return
        if not Variables.is_roblox_focused:     logging.debug("Roblox is not focused."); return
        Variables.is_selling = True

        # try to get the button #
        # tryidx = 0
        # button_pos = None
        # 
        # Mouse.move_mouse(screen_region["width"] // 2, screen_region["height"] // 2)
        # 
        # while Variables.is_running == True and tryidx < 5:
        #     self.toggle_shop()
        # 
        #     button_pos = find_image(self.sell_img, Config.AUTO_SELL_BUTTON_CONFIDENCE, log=True)
        #     if button_pos is not None: break
        # 
        #     time.sleep(0.25)
        #     tryidx = tryidx + 1
        # 
        # if not button_pos or not Variables.is_running or tryidx >= 4:
        #     logging.debug("Button not found.");
        #     Variables.is_selling = False
        #     return
        # 
        # target_x = button_pos["left"] + button_pos["width"] // 2
        # target_y = button_pos["top"]  + button_pos["height"] // 2

        # sell items #
        self.toggle_shop()
        time.sleep(0.5)

        Mouse.move_mouse(*Config.AUTO_SELL_BUTTON_POSITION)
        time.sleep(0.15)
        Mouse.left_click()
        time.sleep(0.15)
        self.toggle_shop()

        self.total_sold = total_sold_add
        Variables.is_selling = False

### FINDER CLASSES ###
# DIRT_BOTTOM_OFFSET = int(21 * scale_y)
# DIRT_BAR_OFFSET = int(40 * scale_y)
# PLAYER_BAR_BOTTOM_OFFSET = int(10 * scale_y)

class PlayerBar:
    def __init__(self):
        self.position = None
        self.current_position = None
        self.bar_in_clickable = False
        
        # prediction
        self.predicted_position = None
        self.current_velocity = 0
        self.current_acceleration = 0
        self.player_bar_tracker = MovementTracker()

        self.mask = None
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))

    def find_bar(self, 
        screenshot, 
        region_left, region_height,
        clickable_position
    ):
        if not clickable_position: return

        player_bar_center = None
        player_bar_bbox = None

        # edit screenshot #
        min_width_bar = 1
        detection = Config.PLAYER_BAR_DETECTION
        
        if detection == "Canny":
            mask = cv2.Canny(screenshot, 600, 600)

        elif detection == "Canny + GaussianBlur":
            mask = cv2.GaussianBlur(screenshot, (3, 3), 0)
            mask = cv2.Canny(mask, 290, 290)

        else:
            min_width_bar = 3
            sobelx = cv2.Sobel(screenshot, cv2.CV_64F, 1, 0, ksize=3)
            mask = cv2.convertScaleAbs(sobelx)

        _, mask = cv2.threshold(mask, Config.PLAYER_BAR_THRESHOLD, 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel) 
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.mask = mask

        # find player bar #
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w >= min_width_bar and h > 15 and h / w > 5.5:
                fixed_x = region_left + (x + w // 2) - 5

                player_bar_bbox = (fixed_x, y, Config.PLAYER_BAR_WIDTH, region_height)
                player_bar_center = fixed_x
                break
        
        if not player_bar_center:
            self.position = None
            self.current_position = None
            return

        # update variables for prediction #
        self.position = player_bar_bbox
        self.update_values(player_bar_center, clickable_position)
    
    # Prediction system #
    def update_values(self, current_left, clickable_position):
        if not current_left: return

        bbox_left, bbox_width = clickable_position[0], clickable_position[2] # clickable_position is always a tuple here #

        self.current_position = current_left
        self.bar_in_clickable = is_pos_in_bbox(current_left, bbox_left, bbox_width)

        if Config.USE_PREDICTION != True: return
        self.player_bar_tracker.update(current_left)
        self.current_velocity = self.player_bar_tracker.get_velocity()
        self.current_acceleration = self.player_bar_tracker.get_acceleration()

        # kinematic equation #
        t = float(Config.PREDICTION_MAX_TIME_AHEAD)
        self.predicted_position = current_left + (self.current_velocity * t) + 0.5 * self.current_acceleration * (t ** 2)

class DirtBar:
    def __init__(self):
        self.position = None
        self.clickable_position = None
        
        self.kernel = np.ones((5, 15), np.uint8)
        self.mask = None

    def find_dirt(self, 
        screenshot,
        region_left, region_top
    ):
        dirt_bar_absolute_position = None

        # edit screenshot #
        _, mask = cv2.threshold(screenshot, Config.DIRT_SATURATION_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.bitwise_not(mask)

        self.mask = mask

        # find dirt part #
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # if 25 < w >= region_width - 5:
            #     self.position = None
            #     self.clickable_position = None
            #     return
            
            dirt_bar_absolute_position = (region_left + x, region_top + y, w, h)

            # set clickable part #
            clickable_width = int(w * Config.DIRT_CLICKABLE_WIDTH)
            clickable_x = x + (w - clickable_width) // 2

            clickable_part_bbox = (
                region_left + clickable_x,
                region_top + y,
                clickable_width,
                h
            )
        else:
            self.position = None
            self.clickable_position = None
            return

        # update variables #
        self.position = dirt_bar_absolute_position
        self.clickable_position = clickable_part_bbox

## MAIN HANDLER FOR CLICKS ##
class MainHandler:
    def __init__(self):
        self.current_fps = 0.0

        # initliaze classes #
        self.PlayerBar = PlayerBar()
        self.DirtBar = DirtBar()

        # click and find variables #
        # self.was_in_zone = False
        # self.just_entered = False
        self.click_cooldown = 0

        # self.last_frame_time = 0
        # self.frame_times = []

        # debug images #
        self.debug_img = None

    def update_state(self, sct):
        if Variables.is_rejoining == True: return
        if Variables.is_roblox_focused == False and Variables.is_selecting_region == False: return
        if Variables.is_selling == True: return
        
        # get offsets #
        region_left, region_top, region_width, region_height = Variables.minigame_region.values()

        # take screenshots #
        screenshot_np = take_screenshot(Variables.minigame_region, sct)
        if screenshot_np is None:
            Variables.is_minigame_active = False
            return
        gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2GRAY)

        if Variables.is_selecting_region == True:
            self.DirtBar.find_dirt( 
                gray_screenshot,
                region_left, region_top
            )

            self.PlayerBar.find_bar(
                gray_screenshot,
                region_left, region_height,
                self.DirtBar.clickable_position
            )

            self.create_debug_image(screenshot_np, region_left)
            return

        # find clickable region #
        self.DirtBar.find_dirt( 
            gray_screenshot,
            region_left, region_top
        )

        # no dirt bar #
        if self.DirtBar.clickable_position is None:
            Variables.is_minigame_active = False
            # self.was_in_zone = False
            return

        # if clickable_position is not none we can update playerBar #
        self.PlayerBar.find_bar(
            gray_screenshot,
            region_left, region_height,
            self.DirtBar.clickable_position
        )

        # no player bar #
        if self.PlayerBar.current_position is None:
            Variables.is_minigame_active = False
            # self.was_in_zone = False
            return
        
        # zone tracking variables #
        # in_zone_now = self.PlayerBar.bar_in_clickable
        # self.just_entered = in_zone_now and not self.was_in_zone
        # self.was_in_zone = in_zone_now

        # enable the minigame #
        Variables.is_minigame_active = True

        # create debug image
        if Config.SHOW_COMPUTER_VISION: self.create_debug_image(screenshot_np, region_left)

    def handle_click(self):
        if not Variables.is_minigame_active or self.PlayerBar.current_position is None:
            return
        
        current_time_ms = int(time.time() * 1000)

        # positions #
        player_bar_center = self.PlayerBar.current_position
        clickable_part = self.DirtBar.clickable_position
        clickable_left, clickable_width = clickable_part[0], clickable_part[2]
        clickable_center = clickable_left + (clickable_width // 2)
        clickable_radius = clickable_width // 2

        # prediction variables #
        confidence = 0.0
        should_click = False
        prediction_used = False
        click_delay = 0

        # verify if we should click or no #
        if (
            current_time_ms >= self.click_cooldown
            and not Mouse.clicking_lock.locked()
        ):
            if Config.USE_PREDICTION:
                predicted_player_bar = self.PlayerBar.predicted_position
                current_velocity = self.PlayerBar.current_velocity

                if predicted_player_bar is not None and abs(current_velocity) >= Config.PREDICTION_MIN_VELOCITY: # check required velocity #
                    player_bar_to_clickable = (player_bar_center < clickable_center) if current_velocity > 0 else (player_bar_center > clickable_center)

                    if player_bar_to_clickable: # check if player bar is going towards clickable part #
                        distance_to_center_PREDICTED = abs(predicted_player_bar - clickable_center)

                        if distance_to_center_PREDICTED <= clickable_radius: # check if prediction bar is inside the clickable part #
                            confidence = 1.0 - (distance_to_center_PREDICTED / clickable_radius)

                            if confidence >= Config.PREDICTION_CONFIDENCE:
                                distance_to_player_bar_CLICKABLE = clickable_center - player_bar_center
                                arrival_in_ms = distance_to_player_bar_CLICKABLE / current_velocity

                                if arrival_in_ms > 0 and arrival_in_ms <= Config.PREDICTION_MAX_TIME_AHEAD: # check if arrival time is under the max time ahead #
                                    should_click, prediction_used, click_delay = True, True, arrival_in_ms
            
                if not should_click:
                    dirt_left, dirt_top, dirt_width, dirt_height = self.DirtBar.clickable_position
                    dirt_half_width = min(0, dirt_width / 2)
                    if dirt_half_width != 0:
                        dirt_bar_center = dirt_left + dirt_half_width

                        # Compute player bar center correctly
                        player_bar_center = self.PlayerBar.current_position

                        center_distance = abs(player_bar_center - dirt_bar_center)
                        normalized_distance = center_distance / dirt_half_width
                        confidence = 1.0 - normalized_distance

                        is_moving_slowly = abs(self.PlayerBar.current_velocity) < 0.25

                        if confidence >= Config.PREDICTION_CENTER_CONFIDENCE:
                            should_click = True
                            prediction_used = True
                        elif is_moving_slowly and confidence >= Config.PREDICTION_SLOW_CONFIDENCE:
                            should_click = True
                            prediction_used = True
            
            if not should_click and self.PlayerBar.bar_in_clickable:
                should_click = True

            # do the click #
            if should_click:
                Mouse.clicking_lock.acquire()
                threading.Thread(target=Mouse.left_click_lock, args=(click_delay,)).start()

                self.click_cooldown = current_time_ms + Config.MIN_CLICK_INTERVAL + click_delay

                Variables.click_count += 1
                Variables.last_minigame_interaction = current_time_ms

                if Config.SHOW_COMPUTER_VISION and Config.PREDICTION_SCREENSHOTS and prediction_used:
                    write_image(os.path.join(StaticVariables.prediction_screenshots_path, str(Variables.click_count) + ("_pred" if prediction_used else "") + ".png"), self.debug_img)

    def create_debug_image(self,
        screenshot_np,
        region_left
    ):
        # Get screenshot dimensions for proper coordinate conversion
        screenshot_height = screenshot_np.shape[:2][0]
        
        # draw the dirt part and clickable part #
        if self.DirtBar.position:
            dx, _, dw, _ = self.DirtBar.position
            cv2.rectangle(screenshot_np, (dx - region_left, 0), (dx - region_left + dw, screenshot_height), (0, 255, 255), 2)
        
        if self.DirtBar.clickable_position:
            cx, _, cw, _ = self.DirtBar.clickable_position
            x1 = int(cx - region_left)
            x2 = int(cx - region_left + cw)
            cv2.rectangle(screenshot_np, (x1, 0), (x2, screenshot_height), (125, 255, 0), 2)

        # draw the player bar (current and prediction) #
        plr_x = self.PlayerBar.current_position
        pred_x = self.PlayerBar.predicted_position

        if plr_x is not None:
            plr_x = int(plr_x - region_left)
            cv2.line(screenshot_np, (plr_x, 0), (plr_x, screenshot_height), (0, 0, 255), Config.PLAYER_BAR_WIDTH)

        if Config.USE_PREDICTION and pred_x is not None:
            pred_x = int(pred_x - region_left)
            cv2.line(screenshot_np, (pred_x, 0), (pred_x, screenshot_height), (255, 0, 255), Config.PLAYER_BAR_WIDTH) 

        # finally set the debug img #
        if Config.SHOW_DEBUG_MASKS:
            self.debug_img = stack_images_with_dividers([ screenshot_np, self.PlayerBar.mask, self.DirtBar.mask ])
        else:
            self.debug_img = stack_images_with_dividers([ screenshot_np ])