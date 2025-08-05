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
        self.enable_prediction = Config.ENABLE_PREDICTION

        self.predicted_position = None
        self.current_velocity = 0
        self.current_acceleration = 0
        self.player_bar_tracker = MovementTracker()

        # kernels and scaling numbers #
        scaling_number = scale_x if scale_factor > 1 else scale_x_1080p

        self.num_kernel = max(3, int(5 * scaling_number))
        self.vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, self.num_kernel))
        
        self.distance_threshold = 10 // scaling_number
        self.margin_offset = 5 // scaling_number
        logging.info(f"Player Bar:\n    - Scaling Factor: {scaling_number} (to 1080p: {scale_x_1080p}, from 1080p: {scale_x})\n    - Kernel NUM: {self.num_kernel}\n    - Distance: {self.distance_threshold}, Margin: {self.margin_offset}")

        # loading #
        detection_method = Config.PLAYER_BAR_DETECTION.lower()       
        if detection_method == "gradient":
            self.find_bar = self._find_bar_gradient
            logging.info("Using 'Gradient' method for player bar.")

        elif detection_method == "zeroslike":
            self.find_bar = self._find_bar_zeroslike
            logging.info("Using 'ZerosLike' method for player bar.")

        else:
            raise ValueError(f"Unknown Player Bar detection method: {Config.PLAYER_BAR_DETECTION}")
        
    # finder handler #
    def _find_bar_zeroslike(self, 
        screenshot, 
        region_left,
        clickable_position
    ):
        if not clickable_position:
            self.update_values(None, clickable_position)
            return
        
        screenshot = screenshot.astype(np.float32) # convert to np float32 array (more accurate for gradient finder) #
            
        # find horizontal gradients by central difference #
        grad_x = np.zeros_like(screenshot)
        grad_x[:, 1:-1] = (screenshot[:, 2:] - screenshot[:, :-2]) / 2.0
        grad_mag = np.abs(grad_x) # absolute gradient to highlight edges #
        
        if self.computer_vision:
            vis_mag = (grad_mag / (grad_mag.max() + 1e-6)) * 255.0
            self.mask = vis_mag.astype(np.uint8)

        column_strength = grad_mag.sum(axis=0) # sum of gradients along vertical axis #
        best_x = np.argmax(column_strength) # use the one line with maximum edge strenght #
        direction_score = grad_x[:, best_x].mean() # get direction for margin offset to put the position in the middle of the player bar #
        
        if direction_score > 0:
            self.update_values(region_left + best_x - self.margin_offset, clickable_position)
        else:
            self.update_values(region_left + best_x + self.margin_offset, clickable_position)

    def _find_bar_gradient(self, 
        screenshot, 
        region_left,
        clickable_position
    ):
        if not clickable_position:
            self.update_values(None, clickable_position)
            return
        
        grad_x = np.gradient(screenshot.astype(np.float32), axis=1)
        grad_mag = np.abs(grad_x)

        if self.computer_vision:
            vis_mag = (grad_mag / (grad_mag.max() + 1e-6)) * 255.0
            self.mask = vis_mag.astype(np.uint8)

        column_strength = np.sum(grad_mag, axis=0)
        best_x = np.argmax(column_strength)
        direction_score = grad_x[:, best_x].mean()
        
        offset = (self.margin_offset * -1) if direction_score > 0 else (self.margin_offset)
        self.update_values(region_left + best_x + offset, clickable_position)

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
        # if self.enable_prediction:
        #     self.player_bar_tracker.update(current_left)
        #     self.current_velocity = self.player_bar_tracker.get_velocity()
        #     self.current_acceleration = self.player_bar_tracker.get_acceleration()
        # 
        #     # kinematic equation #
        #     t = float(Config.PREDICTION_MAX_TIME_AHEAD)
        #     self.predicted_position = current_left + (self.current_velocity * t) + 0.5 * self.current_acceleration * (t ** 2)
