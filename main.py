# Copyright 2025 mstudio45
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Original repository: https://github.com/mstudio45/digmacro
#
# This file may have been modified from its original version.

# imports #
import os, sys, time
import platform, threading

import numpy as np
import cv2
import mss

from pynput.mouse import Controller, Button

# settings #
class Config:
    CLICKABLE_WIDTH = 25
    CHECK_FOR_BLACK_SCREEN = True
    
    # DEBUG WINDOW #
    WINDOW_NAME = "Auto Dig by mstudio45"
    SHOW_DEBUG = True

    # BAR DETECTION SETTINGS (these don't need to be changed, but you can edit them depending on your PC) #
    MIN_BAR_HEIGHT = 30
    MAX_BAR_HEIGHT = 70
    INTENSITY_DIFF_THRESHOLD = 15

###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################

# CODE VARIABLES
is_windows = platform.system() == "Windows"
bar_region = {'left': 535, 'top': 755, 'width': 850, 'height': 125} # DON'T CHANGE THIS (535, 755, 850, 125)

can_click = False
debug_img = None
running = True

# CLICK FUNCTION
_pynput_mouse_controller = Controller()
click = lambda: _pynput_mouse_controller.click(Button.left, 1)

# MAIN BAR HANDLER
black_pixel = np.array([0, 0, 0, 255])
def find_bar(region, sct):
    # cache region variables #
    regionLeft, regionTop, regionWidth, regionHeight = region['left'], region['top'], region['width'], region['height']

    screenshot_np = np.array(sct.grab(region), dtype=np.uint8)

    if Config.CHECK_FOR_BLACK_SCREEN:
        if np.array_equal(screenshot_np[0][0], black_pixel) == False:
            return False, None

    gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # --- 1) Find the Full Bar Region ---
    bar_top_relative = -1
    bar_bottom_relative = -1

    row_averages = np.mean(gray_screenshot, axis=1)
    intensity_diff = np.diff(row_averages)

    potential_tops = np.where(intensity_diff < -Config.INTENSITY_DIFF_THRESHOLD)[0]
    potential_bottoms = np.where(intensity_diff > Config.INTENSITY_DIFF_THRESHOLD)[0]

    for top_idx in potential_tops:
        for bottom_idx in potential_bottoms:
            if bottom_idx > top_idx:
                current_height = bottom_idx - top_idx
                if Config.MIN_BAR_HEIGHT <= current_height <= Config.MAX_BAR_HEIGHT:
                    if top_idx > 0 and bottom_idx < len(row_averages) - 1:
                        avg_outer = (row_averages[top_idx-1] + row_averages[bottom_idx+1]) / 2
                        avg_inner = np.mean(row_averages[top_idx:bottom_idx])
                        if avg_inner < avg_outer * 0.8:
                            bar_top_relative = top_idx
                            bar_bottom_relative = bottom_idx
                            break

        if bar_top_relative != -1:
            break

    if bar_top_relative == -1: # fallback
        bar_top_relative = regionHeight // 2 - 25
        bar_bottom_relative = regionHeight // 2 + 25

    bar_height = bar_bottom_relative - bar_top_relative
    bar_left_offset, bar_top_offset, bar_width = (0, bar_top_relative, regionWidth)
    main_bar_img_gray = gray_screenshot[bar_top_offset : bar_top_offset + bar_height, bar_left_offset : bar_left_offset + bar_width]
   
    # --- 2) Find the player bar ---
    player_bar_center = None
    player_bar_bbox = None

    player_bar_img = gray_screenshot[bar_top_offset : bar_top_offset + bar_height - 35, bar_left_offset : bar_left_offset + bar_width]
    _, white_line_blur_mask = cv2.threshold(player_bar_img, 40, 255, cv2.THRESH_BINARY_INV)

    white_line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 5))
    white_line_mask = cv2.morphologyEx(white_line_blur_mask, cv2.MORPH_OPEN, white_line_kernel)

    player_bar_contours, _ = cv2.findContours(white_line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    potential_player_bar = None

    for contour in player_bar_contours:
        area = cv2.contourArea(contour)
        if area > 100:
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if area / hull_area > 0.7:
                x, y, w, h = cv2.boundingRect(hull)
                center_y = y + h // 2
                potential_player_bar = (x + w - 2, center_y, 5, 10)
            
    if potential_player_bar:
        player_bar_bbox = (regionLeft + bar_left_offset + potential_player_bar[0], regionTop + bar_top_offset, 5, bar_height)

        cx, cy, cw, ch = player_bar_bbox
        player_bar_center = (cx + cw // 2, cy + ch // 2)

    # --- 3) Find the "Dirt Region", IGNORING the player bar ---
    dirt_part_bbox_relative_to_bar = None

    blurred_bar = cv2.GaussianBlur(main_bar_img_gray, (5, 5), 0)
    _, dirt_mask = cv2.threshold(blurred_bar, 40, 255, cv2.THRESH_BINARY_INV)

    if player_bar_bbox: # IGNORE PLAYER BAR
        px, py, pw, ph = player_bar_bbox
        exclude_x1 = max(0, px)
        exclude_y1 = max(0, py)
        exclude_x2 = min(dirt_mask.shape[1], px + pw)
        exclude_y2 = min(dirt_mask.shape[0], py + ph)
        cv2.rectangle(dirt_mask, (exclude_x1, exclude_y1), (exclude_x2, exclude_y2), 0, -1)

    kernel_dirt = np.ones((7, 7), np.uint8)
    dirt_mask = cv2.morphologyEx(dirt_mask, cv2.MORPH_OPEN, kernel_dirt)
    dirt_mask = cv2.bitwise_not(dirt_mask)

    dirt_contours, _ = cv2.findContours(dirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if dirt_contours:
        largest_dirt_contour = max(dirt_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_dirt_contour)
        dirt_part_bbox_relative_to_bar = (x, y, w, h)
    else:
        return False, screenshot_bgr

    # --- 4) Define the "Clickable Part" ---
    clickable_part_bbox = None
    if dirt_part_bbox_relative_to_bar:
        dx, dy, dw, dh = dirt_part_bbox_relative_to_bar
        clickable_x_in_bar = dx + (dw // 2) - (Config.CLICKABLE_WIDTH // 2)
        clickable_part_bbox = (
            regionLeft + bar_left_offset + clickable_x_in_bar,
            regionTop + bar_top_offset + dy,
            Config.CLICKABLE_WIDTH,
            dh
        )

    # --- 5) Check for intersection ---
    is_player_bar_in_clickable_part = False
    if clickable_part_bbox and player_bar_center:
        c_left, _, c_width, _ = clickable_part_bbox
        p_center_x, _ = player_bar_center
        if (p_center_x >= c_left and p_center_x <= c_left + c_width):
            is_player_bar_in_clickable_part = True

    # --- 6) Draw on the Image for Display ---
    if Config.SHOW_DEBUG == True:
        cv2.rectangle(screenshot_bgr, (bar_left_offset, bar_top_offset), (bar_left_offset + bar_width, bar_top_offset + bar_height), (0, 255, 0) if is_player_bar_in_clickable_part else (0, 0, 255), 2)
        
        # draw the dirt part and clickable part #
        if dirt_part_bbox_relative_to_bar:
            dx, dy, dw, dh = dirt_part_bbox_relative_to_bar
            cv2.rectangle(screenshot_bgr, (bar_left_offset + dx, bar_top_offset + dy), (bar_left_offset + dx + dw, bar_top_offset + dy + dh), (255, 0, 255), 2)
        
        if clickable_part_bbox:
            c_left, c_top, c_width, c_height = clickable_part_bbox
            cv2.rectangle(screenshot_bgr, (c_left - regionLeft, c_top - regionTop), (c_left - regionLeft + c_width, c_top - regionTop + c_height), (255, 0, 0), 2)
        
        # draw the player bar #
        if player_bar_bbox:
            p_left, p_top, p_width, p_height = player_bar_bbox
            cv2.rectangle(screenshot_bgr, (p_left - regionLeft, p_top - regionTop), (p_left - regionLeft + p_width, p_top - regionTop + p_height), (0, 50, 255), 2)
        
        if player_bar_center:
            center_x, center_y = player_bar_center
            cv2.circle(screenshot_bgr,  (center_x - regionLeft, center_y - regionTop), 5, (0, 125, 255), -1)

    return is_player_bar_in_clickable_part, screenshot_bgr

# THREADS FOR ASYNC EXECUTION
class HandleDebugWindowThread(threading.Thread):
    # Handles the debug window - if debug is disabled it will open a black window (used for closing the app) #
    def __init__(self, enabled, window_name):
        super().__init__()
        self.enabled = enabled
        self.window_name = window_name

        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        global running, debug_img
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        time.sleep(0.01)
        
        while not self._stop_event.is_set():
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                running = False
                break  
        
            if self.enabled:
                if is_windows == False:
                    os.system(f'wmctrl -r "{self.window_name}" -b add,above')
                else:
                    cv2.setWindowProperty(self.window_name, cv2.WND_PROP_TOPMOST, 1)
                
                if debug_img is not None:
                    cv2.imshow(self.window_name, debug_img)
                cv2.waitKey(1)

    def stop(self):
        self._stop_event.set()
        cv2.destroyWindow(self.window_name)

class PlayerBarThread(threading.Thread):
    # used to find the bar and dirt part #
    def __init__(self, target_region):
        super().__init__()
        self.target_region = target_region

        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        global can_click, debug_img
        sct = mss.mss()

        while not self._stop_event.is_set():
            try:
                can_click, debug_img = find_bar(self.target_region, sct=sct)
            except Exception as e:
                print(e)
            time.sleep(0)

    def stop(self):
        self._stop_event.set()

if __name__ == "__main__":
    last_click_state = False

    # BAR DETECTOR
    player_thread = PlayerBarThread(bar_region)
    player_thread.start()

    # DEBUG WINDOW (Keep Above)
    debug_window_thread = HandleDebugWindowThread(Config.SHOW_DEBUG, Config.WINDOW_NAME)
    debug_window_thread.start()

    # CLICK HANDLER
    try:
        while running:
            if can_click and not last_click_state:
                last_click_state = True
                click()
                time.sleep(0.25)
            else:
                last_click_state = False
            time.sleep(0)

    except KeyboardInterrupt:
        print("Closing...")
    
    except Exception as e:
        print(e)

    finally:
        print("Stopping threads and cleaning up...")
        if debug_window_thread and debug_window_thread.is_alive():
            debug_window_thread.stop()
            debug_window_thread.join(timeout=1)
            if debug_window_thread.is_alive():
                print("Warning: debug_window_thread did not stop gracefully.")

        if player_thread and player_thread.is_alive():
            player_thread.stop()
            player_thread.join(timeout=1)
            if player_thread.is_alive():
                print("Warning: player_thread did not stop gracefully.")

        cv2.destroyAllWindows()
        print("Exited.")
        sys.exit(1)
