# set parent folder imports (used for importing stuff in the current and parent folder (like variables.py)) #
import os, sys
def GetMainDirectory():
    current_dir = os.path.dirname(__file__)
    while True:
        if all(filename in os.listdir(current_dir) for filename in ["variables.py", "main.py"]): break; 
        current_dir = os.path.dirname(current_dir)
    return current_dir
sys.path.append(GetMainDirectory())

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
        while left_location == None and right_location == None and Variables.running == True:
            left_location    = find_image(LEFT_SIDE_IMG,  Config.SIDE_CONFIDENCE)
            right_location   = find_image(RIGHT_SIDE_IMG, Config.SIDE_CONFIDENCE)
            time.sleep(0.1)

        if Variables.running == False:
            sys.exit(1)

        # set the positions in the minigame_region #
        Variables.minigame_region["left"]   = int(right_location["left"]) - int(10 * scale_x)
        Variables.minigame_region["top"]    = int(right_location["top"]) + int(45 * scale_y)

        Variables.minigame_region["width"]  = int(left_location["left"] - right_location["left"]) + int(20 * scale_x)
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

PLAYER_BAR_BOTTOM_PIXELS = 18
class PlayerBar:
    def __init__(self):
        self.position = None
        self.current_position = None
        
        # prediction
        self.predicted_position = None
        self.current_velocity = 0
        self.current_acceleration = 0

        self.player_bar_tracker = MovementTracker()

    def find_bar(self, 
        gray_screenshot, 
        region_left, region_top, 
        bar_left_offset, bar_top_offset, bar_height
    ):
        global PLAYER_BAR_BOTTOM_PIXELS

        player_bar_center = None
        player_bar_bbox = None

        # create a mask to find the contours #
        player_bar_img = gray_screenshot[-PLAYER_BAR_BOTTOM_PIXELS:, :]
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
                    potential_player_bar = (x + w - 1, y + h // 2, 5, 10)
            
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
        self.update_values(player_bar_center)

        # update variables #
        self.mask = player_bar_mask
        self.img = player_bar_img
    
    # Prediction system #
    def update_values(self, new_position):
        if not new_position: return
        self.current_position = new_position

        if Config.USE_PREDICTION != True: return
        
        current_left = new_position[0]
        self.player_bar_tracker.update(current_left)
        self.current_velocity = self.player_bar_tracker.get_velocity()
        self.current_acceleration = self.player_bar_tracker.get_acceleration()

        # kinematic equation #
        t = float(Config.PREDICTION_MAX_TIME_AHEAD)
        self.predicted_position = current_left + (self.current_velocity * t) + (0.5 * self.current_acceleration * (t ** 2));
    
class DirtBar:
    def __init__(self):
        self.position = None
        self.clickable_position = None
        pass

    def find_dirt(self, 
        gray_screenshot,
        region_left, region_top, 
        bar_left_offset, bar_top_offset, bar_height, bar_width
    ):
        dirt_part_bbox_relative_to_bar = None

        dirt_img = gray_screenshot[bar_top_offset + bar_height - 48 : bar_top_offset + bar_height - 18, bar_left_offset : bar_left_offset + bar_width]
        dirt_mask = cv2.GaussianBlur(dirt_img, (5, 5), 0)
        _, dirt_mask = cv2.threshold(dirt_mask, 22, 255, cv2.THRESH_BINARY_INV)

        #if player_bar_bbox:  # IGNORE PLAYER BAR
        #    p_left, p_top, p_width, p_height = player_bar_bbox
        #
        #    bar_relative_x = p_left - regionLeft
        #    bar_relative_y = p_top - regionTop
        #    bar_relative_x -= bar_left_offset
        #    bar_relative_y -= bar_top_offset
        #
        #    x1 = bar_relative_x - player_bar_blur_margin
        #    y1 = bar_relative_y - player_bar_blur_margin
        #    x2 = bar_relative_x + p_width + player_bar_blur_margin
        #    y2 = bar_relative_y + p_height + player_bar_blur_margin
        #    cv2.rectangle(dirt_mask, (x1, y1), (x2, y2), 0, -1)
        
        kernel_dirt = np.ones((7, 7), np.uint8)
        dirt_mask = cv2.morphologyEx(dirt_mask, cv2.MORPH_OPEN, kernel_dirt)
        dirt_mask = cv2.bitwise_not(dirt_mask)

        dirt_contours, _ = cv2.findContours(dirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if dirt_contours:
            largest_dirt_contour = max(dirt_contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_dirt_contour)
            dirt_part_bbox_relative_to_bar = (x, y, w, h)
        else:
            return

        # resize the dirt part to define the clickable part #
        clickable_part_bbox = None
        if dirt_part_bbox_relative_to_bar:
            dx, dy, dw, dh = dirt_part_bbox_relative_to_bar
            clickable_x_in_bar = dx + (dw // 2) - (Config.CLICKABLE_WIDTH // 2)
            clickable_part_bbox = (
                region_left + bar_left_offset + clickable_x_in_bar,
                region_top + bar_top_offset + dy,
                Config.CLICKABLE_WIDTH,
                dh
            )

        # update variables #
        self.position = dirt_part_bbox_relative_to_bar
        self.clickable_position = clickable_part_bbox

        self.mask = dirt_mask
        self.img = dirt_img

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

## MAIN HANDLER FOR CLICKS ##
class MainHandler:
    def __init__(self):
        self.black_pixel = np.array([0, 0, 0, 255])

        self.BarUI = BarUI()
        self.PlayerBar = PlayerBar()
        self.DirtBar = DirtBar()

        # click and find variables #
        self.click_cooldown = 0

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

    def create_debug_image(self, 
        screenshot_bgr,
        region_left, region_top,
        bar_left_offset, bar_top_offset, bar_height, bar_width,

        prediction_used, confidence, click_delay, save_image
    ):
        # draw the dirt part and clickable part #
        if self.DirtBar.position:
            dx, dy, dw, _ = self.DirtBar.position
            cv2.rectangle(screenshot_bgr, (bar_left_offset + dx, bar_top_offset + dy), (bar_left_offset + dx + dw, bar_top_offset + bar_height), (255, 255, 0), 2)
        
        if self.DirtBar.clickable_position:
            c_left, c_top, c_width, _ = self.DirtBar.clickable_position
            cv2.rectangle(screenshot_bgr, (c_left - region_left, c_top - region_top), (c_left - region_left + c_width, bar_top_offset + bar_height), (255, 0, 0), 2)
        
        # draw the player bar (current and prediction) #
        p_top, p_width, p_height = 0, 0, 0
        if self.PlayerBar.position:
            p_left, p_top, p_width, p_height = self.PlayerBar.position
            cv2.rectangle(screenshot_bgr, (p_left - region_left - 2, p_top - region_top - 2), (p_left - region_left + p_width + 2, p_top - region_top + p_height + 2), (0, 0, 255), -1)
            
        if Config.USE_PREDICTION == True:
            if self.PlayerBar.predicted_position is not None:
                predict_left = int(self.PlayerBar.predicted_position)
                cv2.rectangle(screenshot_bgr, (predict_left - region_left - 2, p_top - region_top - 2), (predict_left - region_left + p_width + 2, p_top - region_top + p_height + 2), (255, 0, 255), -1)

        # info img #
        info_img = np.zeros((50, bar_width, 3), dtype=np.uint8)
        debug_text = (f"Pred: {prediction_used} (Conf: {confidence:.2f} - Delay: {click_delay:.5f}) | " if Config.USE_PREDICTION == True else "") + f"Velocity: {self.PlayerBar.current_velocity:.5f}"
        cv2.putText(info_img, debug_text, (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0) if confidence >= Config.PREDICTION_CONFIDENCE else (255, 255, 255), thickness=2)

        # stack masks and imgs and set debug_img #
        self.debug_img = stack_images_with_dividers([
            info_img, screenshot_bgr, 
            # self.DirtBar.img, self.DirtBar.mask,
            # self.PlayerBar.img, self.PlayerBar.mask
        ])

        if save_image == True:
            write_image(f"{StaticVariables.prediction_screenshots_path}/{Variables.click_count}.png", self.debug_img)

    def find_bar(self, custom_sct = None):
        if Variables.roblox_focused == False:
            self.debug_img = self.focus_roblox_img
            return
        
        # create screenshot #
        screenshot_np = take_screenshot(Variables.minigame_region, custom_sct=custom_sct)
        gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2GRAY)

        # get offsets #
        bar_left_offset, bar_top_offset, bar_height, bar_width = self.BarUI.get_offsets()
        region_left, region_top = Variables.minigame_region["left"], Variables.minigame_region["top"]

        # find player bar #
        self.PlayerBar.find_bar(
            gray_screenshot,
            region_left, region_top,
            bar_left_offset, bar_top_offset, bar_height
        )

        # handle minigame active #
        if self.PlayerBar.position:
            Variables.is_minigame_active = True
        else:
            self.debug_img = self.waiting_for_minigame_img
            Variables.is_minigame_active = False
            return

        # find dirt part #
        self.DirtBar.find_dirt( 
            gray_screenshot,
            region_left, region_top, 
            bar_left_offset, bar_top_offset, bar_height, bar_width
        )

        if self.DirtBar.clickable_position is None: return

        # prediction variables #
        current_time = int(time.time() * 1000)

        confidence = 0.0
        should_click, prediction_used = False, False
        click_delay = 0

        # click handler #
        if Variables.is_minigame_active == False: return 
        
        # get player bar center x #
        player_bar_center = self.PlayerBar.current_position[0] if self.PlayerBar.current_position else None
        if player_bar_center is None: return

        # get clickable pos #
        clickable_part_left, _, clickable_part_width, _ = self.DirtBar.clickable_position
        clickable_part_center = clickable_part_left + (clickable_part_width // 2)
        clickable_part_end = clickable_part_center + clickable_part_width / 2
        clickable_radius = clickable_part_width / 2

        # check if predicted position is not None #
        if current_time >= self.click_cooldown and not Inputs.clicking_lock.locked():
            if Config.USE_PREDICTION == True:
                predicted_player_bar = self.PlayerBar.predicted_position
                current_velocity = self.PlayerBar.current_velocity

                if predicted_player_bar is not None and abs(current_velocity) >= Config.PREDICTION_MIN_VELOCITY: # check required velocity #
                    player_bar_to_clickable = (player_bar_center < clickable_part_center) if current_velocity >= 0 else (player_bar_center > clickable_part_center)

                    if player_bar_to_clickable: # check if player bar is going towards clickable part #
                        distance_to_center_PREDICTED = abs(predicted_player_bar - clickable_part_center)

                        if distance_to_center_PREDICTED <= clickable_radius: # check if prediction bar is inside the clickable part #
                            confidence = 1.0 - (distance_to_center_PREDICTED / clickable_radius)

                            if confidence >= 0 and confidence >= Config.PREDICTION_CONFIDENCE: 
                                distance_to_player_bar_CLICKABLE = clickable_part_center - player_bar_center
                                arrival_in_ms = distance_to_player_bar_CLICKABLE / current_velocity

                                if arrival_in_ms > 0 and arrival_in_ms <= Config.PREDICTION_MAX_TIME_AHEAD: # check if arrival time is under the max time ahead #
                                    click_delay = arrival_in_ms
                                    should_click, prediction_used = True, True
                
            # fallback 100% confidence #
            is_player_bar_in_clickable_part = clickable_part_left <= player_bar_center <= clickable_part_end # (player_bar_center >= clickable_part_left and player_bar_center <= clickable_part_left + clickable_part_width)
            if not should_click and is_player_bar_in_clickable_part: # prediction did not find confidence but player bar is in clickable part #
                should_click, click_delay = True, 0
            
            # click handler #
            if should_click:
                self.click_cooldown = current_time + Config.CLICK_COOLDOWN

                Inputs.clicking_lock.acquire()
                threading.Thread(target=Inputs.left_click, args=(click_delay,)).start()

                Variables.click_count = Variables.click_count + 1
                Variables.last_minigame_interaction = current_time

        # create debug image
        if Config.SHOW_DEBUG:
            self.create_debug_image(
                screenshot_np,

                region_left, region_top,
                bar_left_offset, bar_top_offset, bar_height, bar_width,

                prediction_used, confidence, click_delay, 
                (Config.PREDICTION_SCREENSHOTS == True and should_click == True and prediction_used == True)
            )

    def cleanup(self):
        print("[MainHandler.cleanup] Cleaning...")
        screenshot_cleanup()