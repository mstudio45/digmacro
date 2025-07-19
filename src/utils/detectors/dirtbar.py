import numpy as np
import cv2

# file imports #
from config import Config

class DirtBar:
    def __init__(self):
        self.position = None
        self.clickable_position = None
        
        self.computer_vision = Config.SHOW_COMPUTER_VISION and Config.SHOW_DEBUG_MASKS

        self.vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
        self.horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        self.mask = None

        # buffers #
        self._mask_buffer = None
        self._temp_buffer = None
        
    def _ensure_buffers(self, shape):
        if self._mask_buffer is None or self._mask_buffer.shape != shape:
            self._mask_buffer = np.empty(shape, dtype=np.uint8)
            self._temp_buffer = np.empty(shape, dtype=np.uint8)

    def find_dirt(self, screenshot, region_left, region_top):
        self._ensure_buffers(screenshot.shape)

        # edit screenshot #
        if Config.DIRT_DETECTION == "Kernels + GaussianBlur":
            screenshot = cv2.GaussianBlur(screenshot, (3, 3), 0, dst=screenshot) # further remove noise #

        # threshold the background #
        cv2.threshold(screenshot, Config.DIRT_THRESHOLD, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU, dst=self._mask_buffer)

        cv2.morphologyEx(self._mask_buffer, cv2.MORPH_OPEN, self.vertical_kernel, dst=self._mask_buffer) # remove vertical lines #
        cv2.morphologyEx(self._mask_buffer, cv2.MORPH_OPEN, self.horizontal_kernel, dst=self._mask_buffer) # remove horizontal rect #
        cv2.bitwise_not(self._mask_buffer, dst=self._mask_buffer) # flip the detection to include vertical lines and horizontal rect #

        if self.computer_vision: self.mask = self._mask_buffer

        # find dirt part #
        contours, _ = cv2.findContours(self._mask_buffer, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            self.position = None
            self.clickable_position = None
            return

        # find the largest contour #
        areas = [cv2.contourArea(c) for c in contours]
        largest_idx = np.argmax(areas)
        largest_contour = contours[largest_idx]
        
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

        # update variables #
        self.position = dirt_bar_absolute_position
        self.clickable_position = clickable_part_bbox