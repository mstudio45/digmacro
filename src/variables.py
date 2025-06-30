import time, random, string

__all__ = ["Variables", "StaticVariables"]

class Variables:
    running = True

    session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    roblox_focused = False

    # minigame information #
    click_count = 0
    dig_count = 0

    # macro states #
    is_minigame_active = False
    is_walking = False
    is_selling = False
    is_idle = lambda: (Variables.is_walking == False and Variables.is_selling == False and Variables.is_minigame_active == False) == True

    minigame_region = { "left": 0, "top": 0, "width": 0, "height": 0 }
    last_minigame_interaction = -1

class StaticVariables:
    bar_left_side_imgpath = "src/img/left.png"
    bar_right_side_imgpath = "src/img/right.png"
    sell_anywhere_btn_imgpath = "src/img/sell.png"

    position_filepath = "storage/pos.json"
    config_filepath = "storage/config.ini"
    pathfinding_macros_filepath = "storage/pathfinding_macros.json"
    
    screenshots_path = "storage/screenshots"
    prediction_screenshots_path = ""