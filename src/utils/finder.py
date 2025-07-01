import os, sys

# imports #
import time, json, traceback
import cv2
import numpy as np
import pymsgbox, threading

# file imports #
from variables import Variables, StaticVariables
from config import Config

import utils.general.filehandler as FileHandler
from utils.general.screenshots import take_screenshot, cleanup as screenshot_cleanup
import utils.general.input as Inputs
from utils.general.movement_tracker import MovementTracker
from utils.screen_images import *

### IMAGES ###
LEFT_SIDE_IMG  = resize_image(StaticVariables.bar_left_side_imgpath)
RIGHT_SIDE_IMG = resize_image(StaticVariables.bar_right_side_imgpath)
# HEART_IMG = resize_image("img/heart.png")

def is_pos_in_bbox(pos_x, left, width):
    return (pos_x > left and pos_x < left + width)

## SELL ANYWHERE UI ##
class SellUI:
    def __init__(self):
        self.sell_img = resize_image(StaticVariables.sell_anywhere_btn_imgpath)
        self.total_sold = 0
    
    def toggle_shop(self):
        Inputs.press_key("g")
        time.sleep(1)

    def sell_items(self, total_sold_add):
        if not Variables.is_idle(): print("[SellUI.sell_items] Not idle, skipping..."); return
        if not Variables.roblox_focused: print(f"[SellUI.sell_items] Roblox is not focused."); return
        Variables.is_selling = True

        # try to get the button #
        tryidx = 0
        button_pos = None

        while Variables.running == True and tryidx < 5:
            self.toggle_shop()

            button_pos = find_image(self.sell_img, confidence=Config.AUTO_SELL_BUTTON_CONFIDENCE)
            if button_pos is not None: break

        if not button_pos or not Variables.running or tryidx >= 4:
            print(f"[SellUI.sell_items] Button not found.");
            Variables.is_selling = False
            return

        target_x = button_pos["left"] + int(button_pos["width"] / 2)
        target_y = button_pos["top"]  + int(button_pos["height"] / 2)

        # sell items #
        Inputs.move_mouse(target_x, target_y)
        time.sleep(0.1)
        Inputs.left_click()
        time.sleep(0.1)

        self.toggle_shop()
        self.total_sold = total_sold_add

        time.sleep(0.5)
        Variables.is_selling = False

### FINDER CLASSES ###
class BarUI:
    def __init__(self):
        self.MARGIN_OFFSET = 25

    def set_region(self):
        global scale_x, scale_y

        if Config.USE_SAVED_POSITION:
            if os.path.isfile(StaticVariables.position_filepath):
                try:
                    pos = FileHandler.read(StaticVariables.position_filepath)
                    if pos is not None:
                        Variables.minigame_region = json.loads(pos)
                except Exception as e:
                    pymsgbox.alert(f"[BarUI.set_region] Failed to load saved position: \n{traceback.format_exc()}")
                
                if (Variables.minigame_region["left"] == 0 and Variables.minigame_region["top"] == 0 and Variables.minigame_region["width"] == 0 and Variables.minigame_region["height"] == 0) == False:
                    return True

        # try to find the bar UI sides using images #
        left_location, right_location = None, None
        while (left_location == None or right_location == None) and Variables.running == True:
            left_location    = find_image(LEFT_SIDE_IMG,  Config.SIDE_CONFIDENCE)
            right_location   = find_image(RIGHT_SIDE_IMG, Config.SIDE_CONFIDENCE)
            time.sleep(0.1)

        if Variables.running == False:
            sys.exit(1)

        # set the positions in the minigame_region #
        Variables.minigame_region["left"]   = int(right_location["left"]) - int(5 * scale_x)
        Variables.minigame_region["top"]    = int(right_location["top"]) + int(45 * scale_y)

        Variables.minigame_region["width"]  = int(left_location["left"] - right_location["left"]) + int(25 * scale_x)
        Variables.minigame_region["height"] = int(50 * scale_y)

        # save the pos if the config is enabled #
        if Config.USE_SAVED_POSITION:
            FileHandler.write(StaticVariables.position_filepath, json.dumps(Variables.minigame_region))
        
        return True

    def get_offsets(self):
        region_height = Variables.minigame_region["height"]
        bar_top_relative    = region_height // 2 - self.MARGIN_OFFSET
        bar_bottom_relative = region_height // 2 + self.MARGIN_OFFSET

        # bar_left_offset, bar_top_offset, bar_height, bar_width 
        return (0, bar_top_relative, bar_bottom_relative - bar_top_relative, Variables.minigame_region["width"])

PLAYER_BAR_BOTTOM_PIXELS = int(18 * scale_y)
DIRT_BAR_OFFSET = int(40 * scale_y)
class PlayerBar:
    def __init__(self):
        self.position = None
        self.current_position = None

        self.bar_in_clickable = False
        self.predicted_in_clickable = False
        self.in_clickable = False
        
        # prediction
        self.predicted_position = None
        self.current_velocity = 0
        self.current_acceleration = 0

        self.player_bar_tracker = MovementTracker()

    def find_bar(self, 
        screenshot_gray, 
        region_left, region_top, 
        bar_left_offset, bar_top_offset, bar_height,

        clickable_position
    ):
        global PLAYER_BAR_BOTTOM_PIXELS

        player_bar_center = None
        player_bar_bbox = None

        # create a mask to find the contours #
        player_bar_img = screenshot_gray[-PLAYER_BAR_BOTTOM_PIXELS:, :]
        _, player_bar_mask = cv2.threshold(player_bar_img, 20, 255, cv2.THRESH_BINARY_INV)
        player_bar_mask = cv2.GaussianBlur(player_bar_mask, (5, 5), 0)

        player_bar_contours, _ = cv2.findContours(player_bar_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        potential_player_bar = None

        # find hull areas (areas that look like hills) to find the bar rounded end #
        for contour in player_bar_contours:
            area = cv2.contourArea(contour)
            if area > 100:
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                if area / hull_area > 0.7:
                    x, y, w, h = cv2.boundingRect(hull)
                    potential_player_bar = (x + w, y + h // 2, Config.PLAYER_BAR_WIDTH, h)
            
        if potential_player_bar:
            cx, cy, cw, ch = (
                region_left + bar_left_offset + potential_player_bar[0], 
                region_top + bar_top_offset, 
                5, 
                bar_height
            )
            player_bar_bbox = (cx, cy, cw, ch)
            player_bar_center = (cx + cw // 2, cy + ch // 2)

        # update variables for prediction #
        self.position = player_bar_bbox
        self.update_values(player_bar_center, clickable_position)
        self.in_clickable = self.bar_in_clickable and self.predicted_in_clickable

        # update variables #
        self.mask = player_bar_mask
        self.img = player_bar_img
    
    # Prediction system #
    def update_values(self, new_position, clickable_position):
        if not new_position: return

        current_left = new_position[0]
        bbox_left, bbox_width = clickable_position[0], clickable_position[2] # clickable_position is always a tuple here #

        self.current_position = new_position
        self.bar_in_clickable = is_pos_in_bbox(current_left, bbox_left, bbox_width)

        if Config.USE_PREDICTION != True: return
        self.player_bar_tracker.update(current_left)
        self.current_velocity = self.player_bar_tracker.get_velocity()
        self.current_acceleration = self.player_bar_tracker.get_acceleration()

        # kinematic equation #
        t = float(Config.PREDICTION_MAX_TIME_AHEAD)
        self.predicted_position = current_left + (self.current_velocity * t)
        
        if abs(self.current_acceleration) > 100:
            self.predicted_position += 0.5 * self.current_acceleration * (t ** 2)

        self.predicted_in_clickable = is_pos_in_bbox(self.predicted_position, bbox_left, bbox_width)

class DirtBar:
    def __init__(self):
        self.position = None
        self.clickable_position = None
        
        self.kernel = np.ones((5, 15), np.uint8)

    def find_dirt(self, 
        screenshot,
        region_left, region_top, 
        bar_left_offset, bar_top_offset, bar_height, bar_width
    ):
        dirt_part_bbox_relative_to_bar = None

        img = screenshot[bar_top_offset + bar_height - DIRT_BAR_OFFSET : bar_top_offset + bar_height - PLAYER_BAR_BOTTOM_PIXELS, bar_left_offset : bar_left_offset + bar_width]
        # img_hue, _, _ = cv2.split(img)
        # 
        # _, mask = cv2.threshold(img_hue, Config.DIRT_SATURATION_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
        # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        # mask = cv2.bitwise_not(mask)
        # 
        # contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        _, mask = cv2.threshold(img, Config.DIRT_SATURATION_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.bitwise_not(mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_dirt_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_dirt_contour)

            if w >= bar_width - 5:
                self.position = None
                self.clickable_position = None
                return
            
            dirt_part_bbox_relative_to_bar = (x, y, w, h)

            # set clickable part #
            target_width = Config.CLICKABLE_WIDTH
            clickable_x = x + (w - target_width) / 2

            clickable_part_bbox = (
                region_left + bar_left_offset + clickable_x,
                region_top + bar_top_offset + y,
                target_width,
                h
            )
        else:
            self.position = None
            self.clickable_position = None
            return

        # update variables #
        self.position = dirt_part_bbox_relative_to_bar
        self.clickable_position = clickable_part_bbox

        self.mask = mask
        self.img = img

## MAIN HANDLER FOR CLICKS ##
class MainHandler:
    def __init__(self):
        self.black_pixel = np.array([0, 0, 0, 255])

        self.BarUI = BarUI()
        self.PlayerBar = PlayerBar()
        self.DirtBar = DirtBar()

        # click and find variables #
        self.was_in_zone = False
        self.last_click_time = 0
        self.last_frame_time = 0
        self.frame_times = []

        self.current_time_ms = 0

        self.confidence = 0.0
        self.should_click = False
        self.prediction_used = False
        self.click_delay = 0

        # debug images #
        self.debug_img = None

        self.start_minigame_img = np.zeros((50, 350, 3), dtype=np.uint8)
        self.waiting_for_minigame_img = np.zeros((50, 500, 3), dtype=np.uint8)
        self.focus_roblox_img = np.zeros((50, 350, 3), dtype=np.uint8)
        # self.selling_img = np.zeros((50, 350, 3), dtype=np.uint8)

        cv2.putText(self.start_minigame_img, "START MINIGAME", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), thickness=2)
        cv2.putText(self.waiting_for_minigame_img, "WAITING FOR MINIGAME", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 125, 255), thickness=2)
        cv2.putText(self.focus_roblox_img, "FOCUS ROBLOX", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 125, 255), thickness=2)
        # cv2.putText(self.selling_img, "SELLING ITEMS...", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), thickness=2)

    def setup_bar(self):
        print("[MainHandler.setup_bar] Loading Bar UI position...")
        self.debug_img = self.start_minigame_img

        if self.BarUI.set_region() != True:
            pymsgbox.alert("Failed to setup Bar Region.")
            sys.exit(1)
        
        self.debug_img = self.waiting_for_minigame_img

    def update_state(self, custom_sct=None):
        if Variables.roblox_focused == False:
            self.debug_img = self.focus_roblox_img
            return
            
        frame_start_time = time.perf_counter()
        
        # get offsets #
        bar_left_offset, bar_top_offset, bar_height, bar_width = self.BarUI.get_offsets()
        region_left, region_top, _, _ = Variables.minigame_region.values()

        # take screenshots #
        screenshot_np = take_screenshot(Variables.minigame_region, custom_sct=custom_sct)
        gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2GRAY)
        
        # cache hsv #
        # screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2BGR)
        # if not hasattr(self, 'hsv_cache'):
        #     self.hsv_cache = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2HSV)
        # else:
        #     roi = screenshot_bgr[bar_top_offset : bar_top_offset + bar_height, bar_left_offset : bar_left_offset + bar_width]
        #     self.hsv_cache[bar_top_offset : bar_top_offset + bar_height, bar_left_offset : bar_left_offset + bar_width] = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # find clickable region #
        self.DirtBar.find_dirt( 
            gray_screenshot, # self.hsv_cache, # use cache
            region_left, region_top, 
            bar_left_offset, bar_top_offset, bar_height, bar_width
        )

        # handle status #
        if self.DirtBar.clickable_position is None:
            self.debug_img = self.waiting_for_minigame_img
            Variables.is_minigame_active = False
            self.was_in_zone = False
            return
        else:
            Variables.is_minigame_active = True

        # if clickable_position is not none we can update playerBar #
        self.PlayerBar.find_bar(
            gray_screenshot, # convert to gray
            region_left, region_top,
            bar_left_offset, bar_top_offset, bar_height,
            self.DirtBar.clickable_position
        )

        if self.PlayerBar.current_position is None:
            self.debug_img = self.waiting_for_minigame_img
            Variables.is_minigame_active = False
            self.was_in_zone = False
            return
        else:
            Variables.is_minigame_active = True

        # zone tracking variables #
        in_zone_now = self.PlayerBar.bar_in_clickable
        self.just_entered = in_zone_now and not self.was_in_zone
        self.was_in_zone = in_zone_now

        # handle frames and processing time #
        processing_time = (time.perf_counter() - frame_start_time) * 1000
        self.frame_times.append(processing_time)
        if len(self.frame_times) > Config.TARGET_FPS:
            self.frame_times.pop(0)
        
        # create debug image
        if Config.SHOW_DEBUG:
            self.create_debug_image(
                screenshot_np,

                region_left, region_top,
                bar_left_offset, bar_top_offset, bar_height, bar_width,
            )

        # return screenshot_np, bar_left_offset, bar_top_offset, bar_height, bar_width

    def handle_click(self):
        if not Variables.is_minigame_active or self.PlayerBar.current_position is None:
            return
        
        self.current_time_ms = int(time.time() * 1000)

        # positions #
        player_bar_center = self.PlayerBar.current_position[0]
        clickable_part = self.DirtBar.clickable_position
        clickable_center = clickable_part[0] + (clickable_part[2] // 2)
        clickable_radius = clickable_part[2] / 2

        # prediction variables #
        self.confidence = 0.0
        self.should_click = False
        self.prediction_used = False
        self.click_delay = 0

        # verify if we should click or no #
        if (
            self.current_time_ms - self.last_click_time >= Config.MIN_CLICK_INTERVAL and
            self.just_entered and
            not Inputs.clicking_lock.locked()
        ):
            if Config.USE_PREDICTION:
                predicted_player_bar = self.PlayerBar.predicted_position
                current_velocity = self.PlayerBar.current_velocity

                if predicted_player_bar is not None and abs(current_velocity) >= Config.PREDICTION_MIN_VELOCITY: # check required velocity #
                    player_bar_to_clickable = (player_bar_center < clickable_center) if current_velocity >= 0 else (player_bar_center > clickable_center)

                    if player_bar_to_clickable: # check if player bar is going towards clickable part #
                        distance_to_center_PREDICTED = abs(predicted_player_bar - clickable_center)

                        if distance_to_center_PREDICTED <= clickable_radius: # check if prediction bar is inside the clickable part #
                            confidence = 1.0 - (distance_to_center_PREDICTED / clickable_radius)

                            if confidence >= Config.PREDICTION_CONFIDENCE:
                                distance_to_player_bar_CLICKABLE = clickable_center - player_bar_center
                                arrival_in_ms = distance_to_player_bar_CLICKABLE / current_velocity

                                if arrival_in_ms > 0 and arrival_in_ms <= Config.PREDICTION_MAX_TIME_AHEAD: # check if arrival time is under the max time ahead #
                                    self.should_click, self.prediction_used, self.click_delay = True, True, arrival_in_ms
            
            # fallback #
            if not self.should_click and self.PlayerBar.bar_in_clickable:
                self.should_click = True
                # click_delay = 0
                # confidence = 1.0

            # do the click #
            if self.should_click:
                Inputs.clicking_lock.acquire()
                threading.Thread(target=Inputs.left_click, args=(self.click_delay,)).start()

                self.last_click_time = self.current_time_ms
                Variables.click_count += 1
                Variables.last_minigame_interaction = self.current_time_ms

                if Config.SHOW_DEBUG and Config.PREDICTION_SCREENSHOTS:
                    threading.Thread(target=write_image, args=(f"{StaticVariables.prediction_screenshots_path}/{Variables.click_count}{"_pred" if self.prediction_used else ""}.png", self.debug_img,), daemon=True).start()


    def create_debug_image(self, 
        screenshot_np,
        region_left, region_top,
        bar_left_offset, bar_top_offset, bar_height, bar_width
    ):
        # draw the dirt part and clickable part #
        if self.DirtBar.position:
            dx, dy, dw, _ = self.DirtBar.position
            cv2.rectangle(screenshot_np, (bar_left_offset + dx, bar_top_offset + dy), (bar_left_offset + dx + dw, bar_top_offset + bar_height), (255, 255, 0), 2)
        
        if self.DirtBar.clickable_position:
            c_left, c_top, c_width, _ = self.DirtBar.clickable_position
            cv2.rectangle(screenshot_np, (int(c_left - region_left), int(c_top - region_top)), (int(c_left - region_left + c_width), int(bar_top_offset + bar_height)), (255, 0, 0), 2)
        
        # draw the player bar (current and prediction) #
        p_top, p_width, p_height = 0, 0, 0
        if self.PlayerBar.position:
            p_left, p_top, p_width, p_height = self.PlayerBar.position
            cv2.rectangle(screenshot_np, (p_left - region_left - 2, p_top - region_top - 2), (p_left - region_left + p_width, p_top - region_top + p_height), (0, 0, 255), -1)
            
        if Config.USE_PREDICTION == True:
            if self.PlayerBar.predicted_position is not None:
                predict_left = int(self.PlayerBar.predicted_position)
                cv2.rectangle(screenshot_np, (predict_left - region_left - 2, p_top - region_top - 2), (predict_left - region_left + p_width, p_top - region_top + p_height), (255, 0, 255), -1)

        # info img #
        info_img = np.zeros((50, bar_width, 3), dtype=np.uint8)
        debug_text = (f"Pred: {self.prediction_used} (Conf: {self.confidence:.2f} - Delay: {self.click_delay:.3f}) | " if Config.USE_PREDICTION == True else "") + f"Velocity: {self.PlayerBar.current_velocity:.3f} | Time: {self.current_time_ms}"
        cv2.putText(info_img, debug_text, (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.0, (0, 255, 0) if self.confidence >= Config.PREDICTION_CONFIDENCE else (255, 255, 255), thickness=1)

        # stack masks and imgs and set debug_img #
        self.debug_img = stack_images_with_dividers([
            info_img, screenshot_np, 
            # self.DirtBar.img, self.DirtBar.mask,
            # self.PlayerBar.img, self.PlayerBar.mask
        ])

    def cleanup(self):
        print("[MainHandler.cleanup] Cleaning...")
        screenshot_cleanup()