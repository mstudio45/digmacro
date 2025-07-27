import logging
import re
import easyocr

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

        left, top, width, height = Config.DISCORD_STATISTICS_MONEY_POSITION
        self.money_screenshot_region = {"left": left, "top": top, "width": width, "height": height }

        self.money_suffix = {
            "": 1,
            "k": 1000,
            "m": 1000000,
            "b": 1000000000
        }
    
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

    def get_current_money(self):
        image_array = take_screenshot(self.money_screenshot_region)
        if image_array is None:
            return 0
        
        raw_text = self.ocr_util.OCR(image_array)
        money = 0

        try: 
            money = self._format_money(raw_text)
        except Exception as e:
            logging.info(f"Failed to convert OCR result to money: {str(e)}")
        
        return money