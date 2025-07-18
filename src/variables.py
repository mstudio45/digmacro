import os, platform, random, string, shutil, time

__all__ = ["Variables", "StaticVariables"]
current_os = platform.system()

# get compiled paths #
resource_path_str = ""
base_path_str = os.path.abspath(os.getcwd())

if "__compiled__" in globals():
    try:
        from __nuitka_binary_dir import __nuitka_binary_dir # type: ignore
        resource_path_str = __nuitka_binary_dir
    except ImportError: pass

# fix paths #
if current_os == "Darwin" and ".app/Contents/MacOS" in __file__:
    base_path_str = os.path.abspath(os.path.join(__file__[:__file__.find(".app/") + len(".app")], ".."))

if resource_path_str.strip() == "": resource_path_str = os.path.dirname(os.path.abspath(__file__))

# path funcs #
def get_resource_path(*paths): return os.path.join(resource_path_str, *paths)
def get_base_path    (*paths): return os.path.join(base_path_str,     *paths)

# variables #
class Variables:
    is_compiled = "__compiled__" in globals()
    is_running = True
    is_paused = True

    is_roblox_focused = True
    is_selecting_region = True

    # macro settings #
    session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    current_version = "2.0.2"
    current_branch = "main"

    # minigame information #
    dig_count = 0
    click_count = 0
    failed_minigame_attempts = 0
    failed_rejoin_attempts = 0
    
    minigame_region = { "left": 0, "top": 0, "height": 100, "width": 100 }
    last_minigame_detection = None

    # macro states #
    is_minigame_active = False
    is_walking = False
    is_selling = False
    is_rejoining = False
    is_idle = lambda: (Variables.is_rejoining == False and Variables.is_walking == False and Variables.is_selling == False and Variables.is_minigame_active == False) == True

    # cmds #
    unix_open_app_cmd = next((cmd for cmd in ["open", "xdg-open", "gnome-open", "kde-open"] if shutil.which(cmd)), None)
    where_cmd = next((cmd for cmd in ["where", "which"] if shutil.which(cmd)), None)

    # functions #
    def sleep(duration):
        start = time.time()
        
        while Variables.is_running:
            time.sleep(0)
            if time.time() - start >= duration: break

        return Variables.is_running == False

class StaticVariables:
    ui_filepath                 = get_resource_path("assets", "ui", "ui.html")
    guide_ui_filepath           = get_resource_path("assets", "ui", "guide.html")
    region_example_imgpath      = get_resource_path("assets", "select_example.png")

    storage_folder              = get_base_path("storage")
    region_filepath             = os.path.join(storage_folder, "region.json")
    config_filepath             = os.path.join(storage_folder, "config.ini")
    pathfinding_macros_filepath = os.path.join(storage_folder, "pathfinding_macros.json")
    
    logs_path                   = os.path.join(storage_folder, "logs")

    screenshots_path            = os.path.join(storage_folder, "screenshots")
    prediction_screenshots_path = os.path.join(screenshots_path, "prediction", Variables.session_id)