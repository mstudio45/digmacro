import os, time, threading, logging, platform
import cv2

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
        # self.position = None
        self.current_position = None
        self.bar_in_clickable = False
        self.mask = None
        
        # prediction
        self.predicted_position = None
        self.current_velocity = 0
        self.current_acceleration = 0
        self.player_bar_tracker = MovementTracker()

        # kernels and scaling numbers #
        scaling_number = scale_x if scale_factor > 1 else scale_x_1080p

        self.num_kernel = max(3, int(5 * scaling_number))
        self.vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, self.num_kernel))
        self.canny_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, self.num_kernel))
        
        self.distance_threshold = 10 // scaling_number
        self.margin_offset = 5 // scaling_number
        logging.info(f"Player Bar:\n    - Scaling Factor: {scaling_number} (to 1080p: {scale_x_1080p}, from 1080p: {scale_x})\n    - Kernel NUM: {self.num_kernel}\n    - Distance: {self.distance_threshold}, Margin: {self.margin_offset}")

    def find_bar(self, 
        screenshot, 
        region_left,
        clickable_position
    ):
        if not clickable_position:
            self.current_position = None
            self.bar_in_clickable = False
            return
        
        player_bar_center = None
        detection = Config.PLAYER_BAR_DETECTION
        s_height = screenshot.shape[0]

        if detection == "Sobel":
            # edit screenshot #
            mask = cv2.morphologyEx(screenshot, cv2.MORPH_OPEN, self.vertical_kernel) # highlight vertical lines #
            
            sobelx = cv2.Sobel(mask, cv2.CV_64F, 1, 0, ksize=1) # extract edges #
            mask = cv2.convertScaleAbs(sobelx) # convert to abs #
            
            _, mask = cv2.threshold(mask, Config.PLAYER_BAR_SOBEL_THRESHOLD, 255, cv2.THRESH_OTSU) # threshold #
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4) # using contours just ignores the player bar inside the dirt part, force to label everything as its own part #

            self.mask = mask

            # find player bar #
            if num_labels < 2: # player bar has two edges (two lines) #
                self.current_position = None
                self.bar_in_clickable = False
                return
            
            candidate_bars = []
            bar_width = Config.PLAYER_BAR_WIDTH

            for i in range(1, num_labels):
                x, y, w, h, area = stats[i]
                if w <= 1 or abs(h - s_height) > 3 or h / w <= 5: continue
                candidate_bars.append((x, h))

            candidate_bars.sort(key=lambda b: b[0])
            for i in range(len(candidate_bars) - 1):
                x1, h1 = candidate_bars[i]
                x2, h2 = candidate_bars[i + 1]
                
                if h1 == h2 and 0 < x2 - (x1 + bar_width) <= self.distance_threshold:
                    player_bar_center = region_left + (x1 + bar_width // 2) # - 5 # ((x1 + x2) // 2)
                    break
        
        elif "Canny" in detection:
            if detection == "Canny + GaussianBlur":
                mask = cv2.GaussianBlur(screenshot, (3, 3), 0)
                mask = cv2.Canny(mask, 290, 290)
            else:
                mask = cv2.Canny(screenshot, 600, 600)
            
            _, mask = cv2.threshold(mask, Config.PLAYER_BAR_CANNY_THRESHOLD, 255, cv2.THRESH_OTSU) # cv2.THRESH_BINARY + 
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.canny_kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            self.mask = mask

            # find player bar #
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w < 1 or abs(h - s_height) > 3 or h / w <= 5: continue

                player_bar_center = region_left + (x + w // 2) - self.margin_offset
                break
                    
        self.update_values(player_bar_center, clickable_position)
    
    # Prediction system # 
    def update_values(self, current_left, clickable_position):
        if not current_left:
            self.current_position = None
            self.bar_in_clickable = False
            return

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
        
        self.vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
        self.horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        self.mask = None

    def find_dirt(self, 
        screenshot,
        region_left, region_top
    ):
        dirt_bar_absolute_position = None

        # edit screenshot #
        if Config.DIRT_DETECTION == "Kernels + GaussianBlur":
            screenshot = cv2.GaussianBlur(screenshot, (3, 3), 0) # further remove noise #

        # threshold the background #
        _, mask = cv2.threshold(screenshot, Config.DIRT_THRESHOLD, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.vertical_kernel) # remove vertical lines #
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.horizontal_kernel) # remove horizontal rect #
        mask = cv2.bitwise_not(mask) # flip the detection to include vertical lines and horizontal rect #

        self.mask = mask

        # find dirt part #
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea) # vertical lines are always smaller #
            x, y, w, h = cv2.boundingRect(largest_contour)
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

        # variables #
        self.minigame_detected_by_avg = False

        self.click_cooldown = 0
        self.debug_img = None
        self.resized_image_size = (1, 1)
        
    def setup_region_image_size(self):
        if Variables.minigame_region is None: return
        
        _, _, region_width, region_height = Variables.minigame_region.values()
        self.resized_image_size = (int(region_width * scale_x_1080p), int(region_height * scale_y_1080p))
        logging.info(f"Region Image size: ({region_width}, {region_height}) -> {self.resized_image_size}")
    
    def update_state(self, sct):
        if Variables.is_rejoining == True or \
            (Variables.is_roblox_focused == False and Variables.is_selecting_region == False) or \
            Variables.is_selling == True \
        : return
        
        # get offsets #
        region_left, region_top, _, _ = Variables.minigame_region.values()

        # take screenshots #
        screenshot_np = take_screenshot(Variables.minigame_region, sct)
        if screenshot_np is None:
            Variables.is_minigame_active = False
            return
        
        # resize image to 1080p and change to gray_scale #
        if scale_factor > 1: screenshot_np = cv2.resize(screenshot_np, self.resized_image_size, interpolation=cv2.INTER_AREA)
        gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2GRAY)

        # selection region #
        if Variables.is_selecting_region == True:        
            self.DirtBar.find_dirt(gray_screenshot, region_left, region_top)
            self.PlayerBar.find_bar(gray_screenshot, region_left, self.DirtBar.clickable_position)
            self.create_debug_image(screenshot_np, region_left)
            return
        
        # check the minigame #
        avg_color = cv2.mean(screenshot_np[:, :15])[:3]
        self.minigame_detected_by_avg = max(avg_color) - min(avg_color) <= 1
        if self.minigame_detected_by_avg == False:
            Variables.is_minigame_active = False
            return

        # find all stuff #
        self.DirtBar.find_dirt(gray_screenshot, region_left, region_top)
        self.PlayerBar.find_bar(gray_screenshot, region_left, self.DirtBar.clickable_position)
        
        if self.PlayerBar.current_position is None:
            Variables.is_minigame_active = False
            return
        
        # enable the minigame #
        Variables.is_minigame_active = True
        if Config.SHOW_COMPUTER_VISION: self.create_debug_image(screenshot_np, region_left)

    def handle_click(self):
        if not Variables.is_minigame_active: return
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
            current_time_ms >= self.click_cooldown and
            not Mouse.clicking_lock.locked() # clicking lock is used for prediction #
        ):
            if self.PlayerBar.bar_in_clickable:
                should_click = True
            elif Config.USE_PREDICTION:
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
            
                # if not should_click:
                #     dirt_left, dirt_top, dirt_width, dirt_height = self.DirtBar.clickable_position
                #     dirt_half_width = min(0, dirt_width / 2)
                #     if dirt_half_width != 0:
                #         dirt_bar_center = dirt_left + dirt_half_width
                # 
                #         # Compute player bar center correctly
                #         player_bar_center = self.PlayerBar.current_position
                # 
                #         center_distance = abs(player_bar_center - dirt_bar_center)
                #         normalized_distance = center_distance / dirt_half_width
                #         confidence = 1.0 - normalized_distance
                #  
                #         is_moving_slowly = abs(self.PlayerBar.current_velocity) < 0.25
                # 
                #         if confidence >= Config.PREDICTION_CENTER_CONFIDENCE:
                #             should_click = True
                #             prediction_used = True
                #         elif is_moving_slowly and confidence >= Config.PREDICTION_SLOW_CONFIDENCE:
                #             should_click = True
                #             prediction_used = True
                
            # do the click #
            if should_click:
                Mouse.clicking_lock.acquire()
                threading.Thread(target=Mouse.left_click_lock, args=(click_delay,)).start()

                self.click_cooldown = current_time_ms + Config.MIN_CLICK_INTERVAL # + click_delay

                Variables.click_count += 1
                Variables.last_minigame_interaction = current_time_ms

                if prediction_used and Config.PREDICTION_SCREENSHOTS:
                    def screenshot():
                        filename = str(Variables.click_count) + "_pred"

                        write_image(os.path.join(StaticVariables.prediction_screenshots_path, filename + "_found.png"), self.debug_img)
                        time.sleep(click_delay)
                        write_image(os.path.join(StaticVariables.prediction_screenshots_path, filename + "_clicked.png"), self.debug_img)

                    threading.Thread(target=screenshot, daemon=True).start()

    def create_debug_image(self,
        screenshot_np,
        region_left
    ):
        # Get screenshot dimensions for proper coordinate conversion
        screenshot_height = screenshot_np.shape[0]
        
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
        plr_w = Config.PLAYER_BAR_WIDTH

        if plr_x is not None:
            plr_x = int(plr_x - region_left)
            cv2.line(screenshot_np, (plr_x, 0), (plr_x, screenshot_height), (0, 0, 255), plr_w)

        if Config.USE_PREDICTION and pred_x is not None:
            pred_x = int(pred_x - region_left)
            cv2.line(screenshot_np, (pred_x, 0), (pred_x, screenshot_height), (255, 0, 255), plr_w) 

        # finally set the debug img #
        if Config.SHOW_DEBUG_MASKS:
            self.debug_img = stack_images_with_dividers([ screenshot_np, self.PlayerBar.mask, self.DirtBar.mask ])
        else:
            self.debug_img = stack_images_with_dividers([ screenshot_np ])