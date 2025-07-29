import logging
import re
import string
import time

import easyocr
import numpy as np
import cv2

import mss

from utils.images.screenshots import take_screenshot

class OCRUtil:
    def __init__(self):
        self.reader = easyocr.Reader(["en"], gpu=False)

    def OCR(self, image) -> str:
        results = self.reader.readtext(image, detail=0)
        return " ".join(results)

class GameOCR:
    def __init__(self):
        from config import Config
        self.ocr_util = OCRUtil()

        money_left, money_top, money_width, money_height = Config.DISCORD_MONEY_LABEL_REGION
        self.money_screenshot_region = {"left": money_left, "top": money_top, "width": money_width, "height": money_height }
        self.money_suffix = {
            "": 1,
            "k": 1000,
            "m": 1000000,
            "b": 1000000000
        }

        notif_left, notif_top, notif_width, notif_height = Config.DISCORD_ITEM_NOTIFICATION_REGION
        self.notif_screenshot_region = {"left": notif_left, "top": notif_top, "width": notif_width, "height": notif_height }
        self.rarities = [ "Junk", "Common", "Unusual", "Scarce", "Legendary", "Mythical", "Divine", "Prismatic" ]
        self.possible_ending_strings = [ "!", "l" ]
        self.possible_string_split = [ "l dug", "! dug", "l You" ]
        self.dug_up_keyword = [ "dugup", "dug up", "yr old", "you upa ", "you up a" ]

        self.sharp_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    
    # money ocr #
    def _format_money(self, raw_text: str):
        raw_numbers = raw_text.strip().lower().replace("$", "").replace(",", "").replace(" ", "")

        # abbreviated nums #
        if any(raw_numbers.endswith(k) for k in self.money_suffix):
            match = re.match(r'^(\d+\.?\d*)([kmb]?)$', raw_numbers)
            if not match: return 0

            number, suffix = match.groups()
            number = float(number)
            multiplier = self.money_suffix.get(suffix, 1)

            return int(number * multiplier)
        else:
            return int(raw_numbers)

    def get_current_money(self, sct):
        image_array = take_screenshot(self.money_screenshot_region, sct)
        if image_array is None:
            logging.warning("Screenshot returned None; returning 0 as money.")
            return 0
        
        try: 
            raw_text = self.ocr_util.OCR(image_array)
            money = self._format_money(raw_text)
        except Exception as e: 
            logging.info(f"Failed to convert OCR result to money: {str(e)}")
            money = 0
        
        return money
    
    # notification #
    def _clean_ocr_text(self, raw_text):
        cleaned = ''.join(char for char in raw_text if char in string.printable) # remove special unprintable characters #
        cleaned = re.sub(r'[^a-zA-Z0-9\s.,;:!?\'\"()\-]', '', cleaned) # cleanup special keys #
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.lstrip()

    def get_current_item(self, sct):
        screenshot_image = take_screenshot(region=self.notif_screenshot_region, sct=sct)
        if screenshot_image is None: 
            logging.info("Failed to screenshot for item detection.")
            return False, [], "", "", False

        fixed_image = cv2.resize(screenshot_image, None, fx=5, fy=5, interpolation=cv2.INTER_LINEAR)
        fixed_image = cv2.cvtColor(fixed_image, cv2.COLOR_BGRA2GRAY)
        fixed_image = cv2.filter2D(fixed_image, -1, self.sharp_kernel)

        # get raw text #
        raw_text = self.ocr_util.OCR(fixed_image)
        cleaned_text = self._clean_ocr_text(raw_text)
        lower_cleaned_text = cleaned_text.lower()

        # check if it is a new item notif #
        has_keyword = False
        for keyword in self.dug_up_keyword:
            if keyword in lower_cleaned_text:
                has_keyword = True
                break
        
        if not has_keyword: return False, cleaned_text, "", "", False

        # get rarity #
        found_rarity, rarity_position = None, None
        for rarity in self.rarities:
            match = re.search(r'\b' + re.escape(rarity.lower()) + r'\b', lower_cleaned_text)
            if match:
                found_rarity = rarity
                rarity_position = match.start()
                break

        if found_rarity == None or rarity_position == None: return False, cleaned_text, "", "", False

        # get item name #
        item_name = raw_text[rarity_position + len(found_rarity):].lstrip()

        # clear up some random nonsense #
        for split_end in self.possible_string_split:
            idx = item_name.find(split_end)
            if idx != -1:
                item_name = item_name[:idx]
                break
        
        for end in self.possible_ending_strings:
            if item_name.endswith(end):
                item_name = item_name[:-1]
                break
        
        # check if the item is new #
        return True, cleaned_text, item_name, found_rarity, "have discovered" in lower_cleaned_text