import re
import logging

class GameOCR:
    def __init__(self, memory_handler):
        self.memory_handler = memory_handler
        self.money_suffix = {
            "": 1,
            "k": 1000,
            "m": 1000000,
            "b": 1000000000
        }

        self.rarities = [ "Junk", "Common", "Unusual", "Scarce", "Legendary", "Mythical", "Divine", "Prismatic" ]
        self.notifications_handled = []

    def get_current_money(self, sct=None):
        if not self.memory_handler.localPlayerStatsStatsFolder:
            logging.info("Player Stats not found.")
            return 0
        
        try:
            money_instance = self.memory_handler.localPlayerStatsStatsFolder.FindFirstChild("Money")
            if money_instance is None: return 0

            money = int(money_instance.Value)
        except Exception as e: 
            logging.info(f"Failed to get money: {str(e)}")
            money = 0
        
        return money
    
    # notification #
    def get_current_item(self, sct=None):
        if self.memory_handler.notificationFrame is None:
            logging.info("Notification Frame not found.")
            return False, cleaned_text, "", "", False
        
        # get text #
        cleaned_text = ""
        cleaned_text_lower = ""
        is_new = False

        if len(self.notifications_handled) > 3:
            self.notifications_handled = []

        for child in self.memory_handler.notificationFrame.GetChildren():
            if child.raw_address in self.notifications_handled: continue

            childName = child.Name
            if "_Viewport" in childName:
                if cleaned_text == "":
                    text_element = child.FindFirstChild("Title")
                    if text_element is None: print("title not found"); continue

                    cleaned_text = text_element.Text
                    cleaned_text_lower = cleaned_text.lower()
                    
                    self.notifications_handled.append(child.raw_address)
            elif "_Universal" in childName:
                if is_new == False:
                    text_element = child.FindFirstChild("Title")
                    if text_element is None: print("title not found"); continue

                    is_new = "have discovered" in text_element.Text
                    self.notifications_handled.append(child.raw_address)

        # get rarity #
        found_rarity, rarity_position = None, None
        for rarity in self.rarities:
            match = re.search(r'\b' + re.escape(rarity.lower()) + r'\b', cleaned_text_lower)
            if match:
                found_rarity = rarity
                rarity_position = match.start()
                break

        if found_rarity is None or rarity_position is None:
            return False, cleaned_text, "", "", False

        # get item name #
        item_name = cleaned_text[rarity_position + len(found_rarity):].lstrip()
        item_name = item_name.replace("!", "")

        return True, cleaned_text, item_name, found_rarity, is_new
