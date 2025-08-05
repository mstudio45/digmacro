import os
import json
import platform
import configparser
import collections
import ast

from variables import StaticVariables
from utils.general.filehandler import read, write

current_os = platform.system()
current_arch = platform.machine()

all_item_rarities = [
    "Scarce",
    "Legendary",
    "Mythical",
    "Divine",
    "Prismatic",
    "Secret",
]

default_screenshot_package, screenshot_packages = "", []
default_mouse_input_package, mouse_input_packages = "", []
defualt_keyboard_input_package, keyboard_input_packages = "", []
default_detection_method, detection_methods = "", []

if current_os == "Windows":
    default_screenshot_package, screenshot_packages = "bettercam", ["mss", "bettercam"]
    default_mouse_input_package, mouse_input_packages = "win32api", ["win32api", "pynput"]
    defualt_keyboard_input_package, keyboard_input_packages = "pynput", ["pynput"]
    default_detection_method, detection_methods = "OpenCV + OCR", ["OpenCV + OCR", "Memory"]

elif current_os == "Darwin":
    default_screenshot_package, screenshot_packages = "mss", ["mss"]
    default_mouse_input_package, mouse_input_packages = "pynput", ["Quartz", "pynput"]
    defualt_keyboard_input_package, keyboard_input_packages = "Quartz", ["Quartz", "pynput"]
    default_detection_method, detection_methods = "OpenCV + OCR", ["OpenCV + OCR"]

elif current_os == "Linux":
    default_screenshot_package, screenshot_packages = "mss", ["mss"]
    default_mouse_input_package, mouse_input_packages = "pynput", ["pynput"]
    defualt_keyboard_input_package, keyboard_input_packages = "pynput", ["pynput"]
    default_detection_method, detection_methods = "OpenCV + OCR", ["OpenCV + OCR"]

settings_table = {
    # SYSTEM OPTIONS #
    "SYSTEM": {
        "__WARNING": "<b>Memory</b> method reads data straight from the Roblox proccess. <b>USE AT YOUR OWN RISK!</b>" if "Memory" in detection_methods else None,
        "__INFO": "<b>Memory</b> method ignores every <b>region</b>, <b>position</b> option and <b>Minigame</b> section,<br />because they are not required." if "Memory" in detection_methods else None,

        "TARGET_FPS": {
            "widget": "QSpinBox",
            "tooltip": "Target frames per second (FPS) for the macro. [ On Windows, mss locks FPS based on your monitor's refresh rate. ]",
            "min": 1,
            "max": 1000
        },
        "MACOS_DISPLAY_SCALE_OVERRIDE": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Set macOS display scale detection. 0 = auto-detection, 1.0 = standard displays, 2.0 = Retina displays.",
            "min": 0.0,
            "max": 3.0,
            "step": 0.1,
            "enabled": current_os == "Darwin"
        },
        "ENABLE_LOGGING": {
            "widget": "QCheckBox",
            "tooltip": "Enable log files."
        },

        "GLOBAL_DETECTION_METHOD":  {
            "widget": "QComboBox", 
            "tooltip":
                "OpenCV + OCR:\n    - Uses image recognition, image to text models (CPU expensive)" + 
                ("\n\nMemory:\n    - Uses Roblox Memory and syscalls (very fast, doesn't use CPU)\n     - This is against the Roblox Terms Of Service, USE AT YOUR OWN RISK" if "Memory" in detection_methods else ""),
            "items": detection_methods
        }
    },

    # DISCORD BOT OPTIONS #
    "DISCORD": {
        "__WARNING": "⚠ DO NOT SHARE THE BOT TOKEN WITH ANYONE ⚠",
        "__INFO": "Use the <b>/setup</b> command to configure the bot.<br />Make sure the bot has <b>Message Content</b> intent enabled.<br /><b>Item Notifications</b> are not perfect and can sometimes fail or return invalid data.",

        "ENABLE_DISCORD_BOT": {
            "widget": "QCheckBox",
            "tooltip": "Enable the Discord Bot."
        },
        "DISCORD_SHOW_SCREENSHOTS_IN_LOGS": {
            "widget": "QCheckBox",
            "tooltip": "Insert screenshots into messages in the Discord log channel."
        },
        
        "DISCORD_ENABLE_STATISTICS": {
            "widget": "QCheckBox",
            "tooltip": "Enable minigame statistics. (Contains Stats Summary, Money Information)",
        },
        "DISCORD_MINIGAME_INFO_FREQUENCY": {
            "widget": "QSpinBox",
            "tooltip": "Number of digs between sending minigame information.",
            "min": 5,
            "max": 15
        },
        "DISCORD_STATISTICS_INTERVAL": {
            "widget": "QComboBox",
            "tooltip": "Interval for sending statistics.",
            "items": ["1 hour", "30 minutes", "10 minutes"],
        },

        "DISCORD_ENABLE_ITEM_NOTIFICATIONS": {
            "widget": "QCheckBox",
            "tooltip": "Enable notifications for new items.",
        },
        "DISCORD_ITEMS_TO_NOTIFY": {
            "widget": "QMultiComboBox",
            "tooltip": "Select which item rarities to notify.",
            "items": all_item_rarities,   
        },
         "DISCORD_ITEMS_TO_MENTION": {
            "widget": "QMultiComboBox",
            "tooltip": "Select which item rarities to notify with a mention.",
            "items": all_item_rarities,   
        },

        "DISCORD_MONEY_LABEL_REGION": {
            "widget": "QRegionSelector",
            "tooltip": "Region of the money label for statistics tracking. [Required for Statistics]",

            "guide_image": "money_select_example.png",
            "steps": ["Press 'Continue' to start selecting the Money label region."],
            "note": "Make sure that only the money label will be inside the region."
        },
        "DISCORD_ITEM_NOTIFICATION_REGION": {
            "widget": "QRegionSelector",
            "tooltip": "Region of the item notifications. [Required for Item Notifications]",

            "guide_image": "item_notification_select_example.png",
            "steps": ["Press 'Continue' to start selecting the Item Notification region."],
            "note": "Make sure that the region is wide enough to detect mutated items, legendaries etc."
        },

        "DISCORD_USER_ID": {
            "widget": "QLineEdit",
            "tooltip": "Your Discord User ID. [Required for commands]",
        },
        "DISCORD_BOT_TOKEN": {
            "widget": "QLineEdit",
            "tooltip": "Your Discord Bot Token. [ DO NOT SHARE THIS WITH ANYONE ]",
            "password": True,
        },
    },

    # AUTO REJOIN OPTIONS #
    "ROBLOX": {
        "ENABLE_AUTO_REJOIN": {
            "widget": "QCheckBox",
            "tooltip": "Enable automatic rejoining."
        },
        "PRIVATE_SERVER_CODE": {
            "widget": "QLineEdit",
            "tooltip": "Code from your Roblox private server link. (ex: https://www.roblox.com/games/126244816328678/DIG?privateServerLinkCode=XXXXXXXXXXXXXXXXXXXX)"
        },
        "AUTO_REJOIN_INACTIVITY_TIMEOUT": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Inactivity timeout (minutes). Set 0 to disable.",
            "min": 0.0,
            "max": 10.0,
            "step": 0.1
        },
        "AUTO_REJOIN_FAILED_MINIGAME_ATTEMPTS": {
            "widget": "QSpinBox",
            "tooltip": "Number of failed minigame starts before rejoining.",
            "min": 15,
            "max": 200
        },
        "AUTO_REJOIN_ENABLE_PUBLIC_FALLBACK": {
            "widget": "QCheckBox",
            "tooltip": "Allow fallback to public servers after private server failures.",
        },
        "AUTO_REJOIN_FAILED_JOINS_TO_PUBLIC": {
            "widget": "QSpinBox",
            "tooltip": "Number of failed private server rejoins before switching to public servers.",
            "min": 2,
            "max": 10
        },
    },

    # MINIGAME OPTIONS #
    "MINIGAME": {
        "USE_SAVED_POSITION": {
            "widget": "QCheckBox",
            "tooltip": "Save selected regions."
        },
        "AUTO_START_MINIGAME": {
            "widget": "QCheckBox",
            "tooltip": "Automatically start the minigame by clicking."
        },

        "MIN_CLICK_INTERVAL": {
            "widget": "QSpinBox",
            "tooltip": "Minimum interval between clicks (ms).",
            "min": 0,
            "max": 150
        },

        "PLAYER_BAR_DETECTION": {
            "widget": "QComboBox",
            "tooltip": """
ZerosLike: 
    - Recommended for Windows, Intel MacBooks. 
    - Uses 'zeros like' mask to find the player bar using numpy.
Gradient: 
    - Recommended for Linux, Apple Silicon MacBooks.
    - Uses gradient mask to find the player bar using numpy.
    """,
            "items": ["ZerosLike", "Gradient"]
        },
        "PLAYER_BAR_WIDTH": {
            "widget": "QSpinBox",
            "tooltip": "Width of the player bar in pixels.",
            "min": 2,
            "max": 10
        },

        "DIRT_CLICKABLE_WIDTH": {
            "widget": "QDoubleSpinBox",
            "tooltip": "The width of the 'STRONG' clicking area as a percentage of dirt bar width (percentage / 100).",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01
        },
        "DIRT_THRESHOLD": {
            "widget": "QSpinBox",
            "tooltip": "Saturation threshold for detecting dirt area.",
            "min": 0,
            "max": 50
        },
    },
    
    # PATHFINDING OPTIONS #
    "PATHFINDING": {
        "ENABLE_PATHFINDING": {
            "widget": "QCheckBox",
            "tooltip": "Enable pathfinding movement."
        },
        "PATHFINDING_MACRO": {
            "widget": "QComboBox",
            "tooltip": "Select the movement pattern for pathfinding.",
            "items": None
        },
    },
    
    # AUTO SELL OPTIONS #
    "AUTO SELL": {
        "ENABLE_AUTO_SELL": {
            "widget": "QCheckBox",
            "tooltip": "Enable or disable automatic selling (requires Sell Anywhere gamepass)."
        },
        "AUTO_SELL_MODE": {
            "widget": "QComboBox",
            "tooltip": "UI Navigation: Uses Roblox UI Navigation enabled by '\\' key.\nMouse Movement: Uses mouse to click the button (less reliable, semi breaks 'risk_spin', requires AUTO_SELL_BUTTON_POSITION)",
            "items": ["UI Navigation", "Mouse Movement"]
        },
        "AUTO_SELL_BUTTON_POSITION": {
            "widget": "QMousePicker",
            "tooltip": "X and Y position of the 'Sell Inventory' button. (requried for 'Mouse Movement' mode)"
        },
        "AUTO_SELL_REQUIRED_ITEMS": {
            "widget": "QSpinBox",
            "tooltip": "Number of digs before triggering auto-sell.",
            "min": 1,
            "max": 1000
        },
        "AUTO_SELL_AFTER_PATHFINDING_MACRO": {
            "widget": "QCheckBox",
            "tooltip": "Sell automatically when pathfinding macro finishes (ignores items count)."
        },
    },

    # PREDICTION OPTIONS #
    "PREDICTION": {
        "__INFO": "Prediction is <b>temporarily</b> disabled until it's fixed.",

        "ENABLE_PREDICTION": {
            "widget": "QCheckBox",
            "tooltip": "Enable prediction using acceleration and velocity data.",
            
            "enabled": False
        },
        "PREDICTION_MAX_TIME_AHEAD": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Used inside the kinematic equation as the variable 't' (bigger = further prediction, but less reliable).",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,

            "enabled": False
        },
        "PREDICTION_MIN_VELOCITY": {
            "widget": "QSpinBox",
            "tooltip": "Required minimum velocity of the player bar for prediction.",
            "min": 0,
            "max": 1000,
            
            "enabled": False
        },
        "PREDICTION_CONFIDENCE": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Confidence needed for the prediction to trigger a click (0.0 to 1.0).",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
            
            "enabled": False
        },
        "PREDICTION_CENTER_CONFIDENCE": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Minimum confidence required to click when player bar is reasonably centered inside the dirt part.",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
            
            "enabled": False
        },
        "PREDICTION_SLOW_CONFIDENCE": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Minimum confidence required to click when player bar is moving slowly to the center of the dirt part.",
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
            
            "enabled": False
        },
    },

    # PACKAGES OPTIONS #
    "PACKAGES": {
        "MOUSE_INPUT_PACKAGE": {
            "widget": "QComboBox",
            "tooltip": "Select the mouse input package to use.",
            "items": mouse_input_packages
        },
        "KEYBOARD_INPUT_PACKAGE": {
            "widget": "QComboBox",
            "tooltip": "Select the keyboard input package to use.",
            "items": keyboard_input_packages
        },
        "SCREENSHOT_PACKAGE": {
            "widget": "QComboBox",
            "tooltip": "Select the screenshot package to use.",
            "items": screenshot_packages
        },
    },
    
    # GUI OPTIONS #
    "GUI": {
        "UI_ON_TOP": {
            "widget": "QCheckBox",
            "tooltip": "Enable or disable if the UI should appear over everything on the screen."
        },
        "UI_SCALE_OVERRIDE": {
            "widget": "QDoubleSpinBox",
            "tooltip": "Option that makes the UI window smaller or bigger.",
            "min": 0.5,
            "max": 2.5,
            "step": 0.1,
        },
        "SHOW_COMPUTER_VISION": {
            "widget": "QCheckBox",
            "tooltip": "Displays an image with all of the highlighted information that the computer has."
        },
        "SHOW_DEBUG_MASKS": {
            "widget": "QCheckBox",
            "tooltip": "Displays all of the image masks on what the macro sees."
        },
        "DEBUG_IMAGE_FPS": {
            "widget": "QSpinBox",
            "tooltip": "The FPS of the debug image inside the UI window.",
            "min": 1,
            "max": 480,
            "step": 1
        },
    },
    
    # SCREENSHOTS OPTIONS #
    "DEBUG SCREENSHOTS": {
        "PREDICTION_SCREENSHOTS": {
            "widget": "QCheckBox",
            "tooltip": "Enables making screenshots for each prediction clicks (requires 'Show Debug' to be enabled).",
            
            "enabled": False
        },
        "SCREENSHOT_EVERY_CLICK": {
            "widget": "QCheckBox",
            "tooltip": "Enables making screenshots for each click (requires 'Show Debug' to be enabled)."
        },
    },

    "default": {
        "widget": "QLineEdit",
        "tooltip": "Configuration value for {key}."
    }
}

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file

        self.config = {}
        self.PathfindingMacros = {}

        self._set_default_config()
        # self.load_config()

    def _set_default_config(self):
        self.default_config = {
            "SYSTEM": {
                "TARGET_FPS": 60 if current_os == "Darwin" and current_arch == "x86_64" else 120,
                "MACOS_DISPLAY_SCALE_OVERRIDE": 0.0,
                "ENABLE_LOGGING": True,
                "GLOBAL_DETECTION_METHOD": "OpenCV + OCR"
            },

            "DISCORD": {
                "ENABLE_DISCORD_BOT": False,
                "DISCORD_SHOW_SCREENSHOTS_IN_LOGS": True,                
                "DISCORD_MINIGAME_INFO_FREQUENCY": 5, 

                "DISCORD_ENABLE_STATISTICS": True,
                "DISCORD_STATISTICS_INTERVAL": "30 minutes",
                "DISCORD_MONEY_LABEL_REGION": (0, 0, 0, 0),

                "DISCORD_ENABLE_ITEM_NOTIFICATIONS": True,
                "DISCORD_ITEMS_TO_NOTIFY": all_item_rarities,
                "DISCORD_ITEMS_TO_MENTION": [],
                "DISCORD_ITEM_NOTIFICATION_REGION": (0, 0, 0, 0),

                "DISCORD_USER_ID": "",
                "DISCORD_BOT_TOKEN": "",
            },

            "ROBLOX": {
                "ENABLE_AUTO_REJOIN": False,
                "PRIVATE_SERVER_CODE": "",

                "AUTO_REJOIN_INACTIVITY_TIMEOUT": 2.5,

                "AUTO_REJOIN_FAILED_MINIGAME_ATTEMPTS": 15,

                "AUTO_REJOIN_ENABLE_PUBLIC_FALLBACK": True,
                "AUTO_REJOIN_FAILED_JOINS_TO_PUBLIC": 5,
            },

            "MINIGAME": {
                "USE_SAVED_POSITION": True,

                "AUTO_START_MINIGAME": False,
                "MIN_CLICK_INTERVAL": 75,

                "PLAYER_BAR_DETECTION": "ZerosLike" if current_os == "Windows" or current_arch == "x86_64" else "Gradient",
                "PLAYER_BAR_WIDTH": 5,

                "DIRT_CLICKABLE_WIDTH": 0.125,
                "DIRT_THRESHOLD": 25,
            },

            "PATHFINDING": {
                "ENABLE_PATHFINDING": False,
                "PATHFINDING_MACRO": "square",
            },

            "AUTO SELL": {
                "ENABLE_AUTO_SELL": False,
                "AUTO_SELL_MODE": "UI Navigation",
                "AUTO_SELL_BUTTON_POSITION": (0, 0),

                "AUTO_SELL_REQUIRED_ITEMS": 15,
                "AUTO_SELL_AFTER_PATHFINDING_MACRO": False
            },

            "PREDICTION": {
                "ENABLE_PREDICTION": False,

                "PREDICTION_MAX_TIME_AHEAD": 0.05,
                "PREDICTION_MIN_VELOCITY": 300,

                "PREDICTION_CONFIDENCE": 0.8,
                "PREDICTION_CENTER_CONFIDENCE": 0.875,
                "PREDICTION_SLOW_CONFIDENCE": 0.7,
            },

            "PACKAGES": {
                "MOUSE_INPUT_PACKAGE": default_mouse_input_package,
                "KEYBOARD_INPUT_PACKAGE": defualt_keyboard_input_package,
                "SCREENSHOT_PACKAGE": default_screenshot_package,
            },

            "GUI": {
                "UI_ON_TOP": True,
                "UI_SCALE_OVERRIDE": 1.0,
                "SHOW_COMPUTER_VISION": True,
                "SHOW_DEBUG_MASKS": False,
                "DEBUG_IMAGE_FPS": 60
            },

            "DEBUG SCREENSHOTS": {
                "PREDICTION_SCREENSHOTS": False,
                "SCREENSHOT_EVERY_CLICK": False
            }
        }

        self.default_PathfindingMacros = {
            "square": [["w", 1.0], ["d", 1.0], ["s", 1.0], ["a", 1.0]],
            "big_square": [["w", 1.5], ["d", 1.5], ["s", 1.5], ["a", 1.5]],
            "rectangle": [["w", 1.0], ["d", 0.5], ["s", 1.0], ["a", 0.5]],
            "big_rectangle": [["w", 1.5], ["d", 1.0], ["s", 1.5], ["a", 1.0]],
            "hexagon": [
                ["w", 0.5], [["w", "d"], 0.5],
                ["d", 0.5], [["s", "d"], 0.5],
                ["s", 0.5], [["s", "a"], 0.5],
                ["a", 0.5], [["w", "a"], 0.5]
            ],
            "triangle_right": [
                ["w", 0.6], [["s", "d"], 0.75], [["s", "a"], 0.75],
            ],
            "triangle_left": [
                [["w", "a"], 0.75], [["w", "d"], 0.75], ["s", 0.6]
            ],
            "double_triangle": [
                ["w", 0.6], [["s", "d"], 0.75], [["s", "a"], 0.75],
                [["w", "a"], 0.75], [["w", "d"], 0.75], ["s", 0.6]
            ],
            "diamond": [
                [["w", "d"], 0.5], [["s", "d"], 0.5], [["s", "a"], 0.5], [["w", "a"], 0.5]
            ],
            "figure_eight": [
                ["w", 0.5], [["w", "d"], 0.5], ["d", 0.5], [["s", "d"], 0.5],
                ["s", 0.5], [["s", "a"], 0.5], ["a", 0.5], [["w", "a"], 0.5],
                ["w", 0.5], [["w", "a"], 0.5], ["a", 0.5], [["s", "a"], 0.5],
                ["s", 0.5], [["s", "d"], 0.5], ["d", 0.5], [["w", "d"], 0.5]
            ],
            "cross": [
                ["w", 0.5], ["w", 0.5], ["s", 1.5], ["s", 0.5], ["w", 1.0],
                ["d", 0.5], ["d", 0.5], ["a", 1.5], ["a", 0.5], ["d", 1.0]
            ],
            "zigzag": [
                [["w", "d"], 0.4], [["w", "a"], 0.4], [["w", "d"], 0.4],
                [["w", "a"], 0.4], [["w", "d"], 0.4], [["w", "a"], 0.4],
                [["s", "d"], 0.4], [["s", "a"], 0.4], [["s", "d"], 0.4],
                [["s", "a"], 0.4], [["s", "d"], 0.4], [["s", "a"], 0.4]
            ],
            "l_shape": [
                ["w", 0.5], ["w", 0.5], ["d", 0.5],
                ["a", 0.5], ["s", 1.0]
            ],
            "t_shape": [
                ["w", 0.5], ["w", 0.5], ["d", 0.5], ["a", 1.0],
                ["d", 0.5], ["s", 1.0]
            ],
        }

        # copy the tables #
        self.config = self.default_config.copy()
        self.PathfindingMacros = self.default_PathfindingMacros.copy()

        # set the default config #
        for section in self.config:
            for key in self.config[section]:
                setattr(self, key, self.config[section][key])

    def _format_pathfinding_macros(self):
        macro_strings = []
        for name, keys in self.PathfindingMacros.items():
           if name == "risk_spin": continue

           keys_string = json.dumps(keys)[1:][:-1]
           macro_strings.append(f'    "{name}": [\n        {keys_string}\n    ]')

        macros_content = ",\n".join(macro_strings)
        final_json_string = "{\n" + macros_content + "\n}"

        return final_json_string

    def load_config(self):
        print("Loading config...")
        
        if not os.path.exists(self.config_file):
            print(f"[ConfigManager.load_config] Config file '{self.config_file}' not found. Using default settings.")

            self._set_default_config()
            self.save_config()
            return True
        
        parser = configparser.ConfigParser()
        parser.read(self.config_file)

        # load config #
        for section in self.config:
            if section not in parser:
                continue
            if section.startswith("__"):
                continue
            
            for key in self.config[section]:
                try:
                    if isinstance(self.config[section][key], bool):
                        value = parser.getboolean(section, key)

                        self.config[section][key] = parser.getboolean(section, key)
                        setattr(self, key, value)

                    elif isinstance(self.config[section][key], int):
                        value = parser.getint(section, key)

                        self.config[section][key] = parser.getint(section, key)
                        setattr(self, key, value)

                    elif isinstance(self.config[section][key], float):
                        value = parser.getfloat(section, key)

                        self.config[section][key] = value
                        setattr(self, key, value)

                    else:
                        value = parser.get(section, key)
                        try:
                            parsed = ast.literal_eval(value)
                            value = parsed
                        except (ValueError, SyntaxError):
                            pass
                        
                        self.config[section][key] = value
                        setattr(self, key, value)

                except ValueError:
                    print(f"[ConfigManager.load_config] Warning: Could not parse config value for '[{section}]{key}'. Using default.")

                except configparser.NoOptionError:
                    print(f"[ConfigManager.load_config] Warning: Option '[{section}]{key}' not found in config file. Using default.")
    
        # load PathfindingMacros #
        if os.path.isfile(StaticVariables.pathfinding_macros_filepath):
            try:
                data = json.loads(read(StaticVariables.pathfinding_macros_filepath))

                new_data = collections.OrderedDict()
                new_data["risk_spin"] = [] # one place dig #
                new_data.update(data)

                self.PathfindingMacros = new_data
            except json.JSONDecodeError:
                print("[ConfigManager.load_config] Warning: Could not decode 'PathfindingMacros' from config file. Using defaults.")
        else:
            print(f"[ConfigManager.load_config] Pathfinding macros file '{StaticVariables.pathfinding_macros_filepath}' not found. Using default macros.")
            
            new_data = collections.OrderedDict()
            new_data["risk_spin"] = [] # one place dig #
            new_data.update(self.default_PathfindingMacros.copy())
            
            self.PathfindingMacros = new_data

        return False

    def save_config(self):
        parser = configparser.ConfigParser()
        parser["__WARNING__"] = {
            "1": "!!! REMOVE THE DISCORD BOT TOKEN BEFORE SHARING YOUR CONFIG   !!!",
            "2": "!!!         EXPOSING YOUR DISCORD BOT TOKEN CAN LEAD          !!!",
            "3": "!!!             TO YOUR BOT BEING COMPROMISED                 !!!"
        }

        for section, options in self.config.items():
            parser[section] = {}
            
            for k, v in options.items():
                key, val = str(k), None

                if isinstance(v, (list, dict, bool, type(None), float, int)):
                    val = repr(v)
                else:
                    val = str(v)
                
                parser[section][key] = val
        
        # save as json #
        write(StaticVariables.pathfinding_macros_filepath, self._format_pathfinding_macros())

        # save as ini #
        with open(self.config_file, 'w') as f:
            parser.write(f)
            f.close()

    # setter #
    def set(self, section, key, value, save_config=True):
        if section in self.config and key in self.config[section]:
            setattr(self, key, value)
            self.config[section][key] = value
            if save_config: self.save_config() # instant save #
        else:
            raise ValueError(f"[ConfigManager.set] Section '{section}' or key '{key}' not found in configuration.")

    # reset #
    def reset_to_defaults(self):
        self._set_default_config()
        self.save_config()
        print("[ConfigManager.reset_to_defaults] Configuration reset to default values.")

    # Config[key] support #
    def __getitem__(self, key):
        return getattr(self, key)

# load classes #
Config = ConfigManager(StaticVariables.config_filepath)