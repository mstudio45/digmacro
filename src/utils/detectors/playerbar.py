import logging
import numpy as np
import cv2

# file imports #
from config import Config
from utils.general.movement_tracker import MovementTracker
from utils.images.screen import scale_x, scale_x_1080p, scale_factor

def is_pos_in_bbox(pos_x, left, width):
    return left <= pos_x <= (left + width)

class PlayerBar:
    def __init__(self):
        # self.position = None
        self.current_position = None
        self.bar_in_clickable = False
        self.mask = None
        
        self.computer_vision = Config.SHOW_COMPUTER_VISION and Config.SHOW_DEBUG_MASKS

        # prediction
        self.use_prediction = Config.USE_PREDICTION

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

        # buffers #
        self._temp_mask = None

    # finder handler #
    def _ensure_buffers(self, shape):
        if self._temp_mask is None:
            self._temp_mask = np.empty(shape, dtype=np.uint8)
        
        elif self._temp_mask.shape != shape:
            del self._temp_mask
            self._temp_mask = np.empty(shape, dtype=np.uint8)

    if Config.PLAYER_BAR_DETECTION == "Canny":
        logging.info("Using 'Canny' method for player bar.")
        def find_bar(self, 
            screenshot, 
            region_left,
            clickable_position
        ):
            if not clickable_position:
                self.current_position = None
                self.bar_in_clickable = False
                return
            
            # create the mask #
            self._ensure_buffers(screenshot.shape)
            s_height = screenshot.shape[0]

            canny = cv2.Canny(screenshot, 600, 600, apertureSize=3)
            cv2.threshold(canny, Config.PLAYER_BAR_CANNY_THRESHOLD, 255, cv2.THRESH_OTSU, dst=self._temp_mask) # cv2.THRESH_BINARY + 
            cv2.morphologyEx(self._temp_mask, cv2.MORPH_OPEN, self.canny_kernel, dst=self._temp_mask)
            
            contours, _ = cv2.findContours(self._temp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if self.computer_vision: self.mask = self._temp_mask

            # find player bar #
            player_bar_center = None
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w >= 1 and abs(h - s_height) <= 3 and h / w > 5:
                    player_bar_center = region_left + (x + w // 2) - self.margin_offset
                    break
                    
            self.update_values(player_bar_center, clickable_position)
    
    elif Config.PLAYER_BAR_DETECTION == "ZerosLike":
        logging.info("Using 'ZerosLike' method for player bar.")
        def find_bar(self, 
            screenshot, 
            region_left,
            clickable_position
        ):
            if not clickable_position:
                self.current_position = None
                self.bar_in_clickable = False
                return
            
            screenshot = screenshot.astype(np.float32) # convert to np float32 array (more accurate for gradient finder) #
            
            # find horizontal gradients by central difference #
            grad_x = np.zeros_like(screenshot)
            grad_x[:, 1:-1] = (screenshot[:, 2:] - screenshot[:, :-2]) / 2.0
            grad_mag = np.abs(grad_x) # absolute gradient to highlight edges #
            
            column_strength = grad_mag.sum(axis=0) # sum of gradients along vertical axis #
            best_x = np.argmax(column_strength) # use the one line with maximum edge strenght #
            direction_score = grad_x[:, best_x].mean() # get direction for margin offset to put the position in the middle of the player bar #
            
            if direction_score > 0:
                self.update_values(region_left + best_x - self.margin_offset, clickable_position)
            else:
                self.update_values(region_left + best_x + self.margin_offset, clickable_position)
    
    else:
        logging.info("Using 'Gradient' method for player bar.")
        def find_bar(self, 
            screenshot, 
            region_left,
            clickable_position
        ):
            if not clickable_position:
                self.current_position = None
                self.bar_in_clickable = False
                return
            
            grad_x = np.gradient(screenshot.astype(np.float32), axis=1)
            grad_mag = np.abs(grad_x)

            if self.computer_vision: self.mask = np.clip((grad_mag / grad_mag.max()) * 255.0, 0, 255).astype(np.uint8)

            column_strength = np.sum(grad_mag, axis=0)
            best_x = np.argmax(column_strength)
            direction_score = grad_x[:, best_x].mean()
            
            if direction_score > 0:
                self.update_values(region_left + best_x - self.margin_offset, clickable_position)
            else:
                self.update_values(region_left + best_x + self.margin_offset, clickable_position)

    # Prediction system # 
    def update_values(self, current_left, clickable_position):
        if current_left is None:
            self.current_position = None
            self.bar_in_clickable = False
            return

        bbox_left, bbox_width = clickable_position[0], clickable_position[2] # clickable_position is always a tuple here #

        self.current_position = current_left
        self.bar_in_clickable = is_pos_in_bbox(current_left, bbox_left, bbox_width)

        # prediction #
        # if self.use_prediction:
        #     self.player_bar_tracker.update(current_left)
        #     self.current_velocity = self.player_bar_tracker.get_velocity()
        #     self.current_acceleration = self.player_bar_tracker.get_acceleration()
        # 
        #     # kinematic equation #
        #     t = float(Config.PREDICTION_MAX_TIME_AHEAD)
        #     self.predicted_position = current_left + (self.current_velocity * t) + 0.5 * self.current_acceleration * (t ** 2)
