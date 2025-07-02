import os, random, string

__all__ = ["Variables", "StaticVariables"]

if "__compiled__" in globals():
    base_path = os.path.dirname(__file__)
    try:
        from __nuitka_binary_dir import __nuitka_binary_dir # type: ignore
        base_path = __nuitka_binary_dir
    except ImportError: pass
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    return os.path.join(base_path, relative_path)

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
    is_rejoining = False
    is_idle = lambda: (Variables.is_rejoining == False and Variables.is_walking == False and Variables.is_selling == False and Variables.is_minigame_active == False) == True

    minigame_region = { "left": 0, "top": 0, "width": 0, "height": 0 }
    last_minigame_interaction = -1

class StaticVariables:
    bar_left_side_imgpath       = resource_path("img/left.png")
    bar_right_side_imgpath      = resource_path("img/right.png")
    sell_anywhere_btn_imgpath   = resource_path("img/sell.png")
    gamepass_shop_btn_imgpath   = resource_path("img/gamepass_shop.png")
    reconnect_btn_imgpath       = resource_path("img/reconnect.png")

    position_filepath = "storage/pos.json"
    config_filepath = "storage/config.ini"
    pathfinding_macros_filepath = "storage/pathfinding_macros.json"
    
    logs_path = "storage/logs"

    screenshots_path = "storage/screenshots"
    prediction_screenshots_path = ""