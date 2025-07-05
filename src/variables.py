import os, random, string, shutil, time

__all__ = ["Variables", "StaticVariables"]

# get onefile compiled path #
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

# variables #
class Variables:
    is_compiled = "__compiled__" in globals()
    is_running = True

    session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    is_roblox_focused = True
    is_selecting_region = True

    # minigame information #
    dig_count = 0
    click_count = 0
    
    minigame_region = { "left": 0, "top": 0, "height": 100, "width": 100 }
    last_minigame_interaction = None

    # macro states #
    is_minigame_active = False
    is_walking = False
    is_selling = False
    is_rejoining = False
    is_idle = lambda: (Variables.is_rejoining == False and Variables.is_walking == False and Variables.is_selling == False and Variables.is_minigame_active == False) == True

    # cmds #
    unix_macos_open_cmd = next((cmd for cmd in ["open", "xdg-open", "gnome-open", "kde-open"] if shutil.which(cmd)), None)

    # functions #
    def sleep(duration):
        start = time.time()
        
        while Variables.is_running:
            time.sleep(0)
            if time.time() - start >= duration: break

        return Variables.is_running == False

class StaticVariables:
    ui_filepath                 = resource_path(os.path.join("assets", "ui", "ui.html"))
    guide_ui_filepath           = resource_path(os.path.join("assets", "ui", "guide.html"))

    sell_anywhere_btn_imgpath   = resource_path(os.path.join("assets", "sell.png"))
    topbar_btns_imgpath         = resource_path(os.path.join("assets", "topbar_btns.png"))
    reconnect_btn_imgpath       = resource_path(os.path.join("assets", "reconnect.png"))
    region_example_imgpath      = resource_path(os.path.join("assets", "select_example.png"))

    region_filepath = os.path.join("storage", "region.json")
    config_filepath = os.path.join("storage", "config.ini")
    pathfinding_macros_filepath = os.path.join("storage", "pathfinding_macros.json")
    
    logs_path = os.path.join("storage", "logs")

    screenshots_path = os.path.join("storage", "screenshots")
    prediction_screenshots_path = os.path.join(screenshots_path, "prediction", Variables.session_id)