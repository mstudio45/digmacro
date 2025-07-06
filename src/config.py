import os, json, platform
import configparser

from variables import StaticVariables
from utils.general.filehandler import read, write

current_os = platform.system()

# this shit pmo fr #
screenshot_packages = []
mouse_input_packages = []

if current_os == "Windows":
    screenshot_packages = ["bettercam", "mss"]
    mouse_input_packages = ["win32api", "pynput"]

elif current_os == "Darwin":
    screenshot_packages = ["mss"]
    mouse_input_packages = ["Quartz", "pynput"]

elif current_os == "Linux":
    screenshot_packages = ["mss"]
    mouse_input_packages = ["pynput"]

settings_table = {
    "TARGET_FPS": {
        "widget": "QSpinBox",
        "tooltip": "Target Frames Per Second for the macro.",
        "min": 1,
        "max": 480
    },
    "MACOS_DISPLAY_SCALE_OVERRIDE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Override macOS display scale detection. Set to 0 for auto-detection, 1.0 for standard displays, 2.0 for Retina displays.",
        "min": 0.0,
        "max": 3.0,
        "step": 0.1
    },
    "LOGGING_ENABLED": {
        "widget": "QCheckBox",
        "tooltip": "Enable or disable log files."
    },
    "MSGBOX_ENABLED": {
        "widget": "QCheckBox",
        "tooltip": "Enable or disable the error message boxes."
    },

    "AUTO_REJOIN": {
        "widget": "QCheckBox",
        "tooltip": "Enable or disable the rejoining system."
    },
    "PRIVATE_SERVER_CODE": {
        "widget": "QLineEdit",
        "tooltip": "Your private server code. (the code from this link: https://www.roblox.com/games/126244816328678/DIG?privateServerLinkCode=XXXXXXXXXXXXXXXXXXXX)"
    },
    "AUTO_REJOIN_INACTIVITY_TIMEOUT": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Inactivity timeout used for Auto Rejoin (in minutes).",
        "min": 0.5,
        "max": 10.0,
        "step": 0.1
    },
    "AUTO_REJOIN_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Used in Auto Rejoin to find the Gamepass Shop button to see if the rejoin was successful.",
        "min": 0.35,
        "max": 1.0,
        "step": 0.01
    },
    "AUTO_REJOIN_RECONNECT_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Used in Auto Rejoin to check if the reconnect button (in the 'Disconnected' menu) is on the screen.",
        "min": 0.35,
        "max": 1.0,
        "step": 0.01
    },

    
    "USE_SAVED_POSITION": {
        "widget": "QCheckBox",
        "tooltip": "Only find the player UI once (delete storage/pos.json file to reset the saved UI position)."
    },
    "AUTO_START_MINIGAME": {
        "widget": "QCheckBox",
        "tooltip": "Auto clicks to start the minigame so you don't need to use an auto clicker."
    },

    "MIN_CLICK_INTERVAL": {
        "widget": "QSpinBox",
        "tooltip": "Minimum time between clicks (in milliseconds).",
        "min": 0,
        "max": 150
    },

    "CLICKABLE_WIDTH": {
        "widget": "QDoubleSpinBox",
        "tooltip": "The width of the 'STRONG' clicking area as a percentage of dirt bar width (percentage / 100).",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
        "default": 0.1
    },
    "PLAYER_BAR_WIDTH": {
        "widget": "QSpinBox",
        "tooltip": "The width of the player bar.",
        "min": 2,
        "max": 10
    },

    "MIN_CENTER_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Minimum confidence required to click when player bar is reasonably centered.",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
        "default": 0.9
    },
    "MIN_SLOW_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Minimum confidence required to click when player bar is moving slowly.",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
        "default": 0.85
    },

    "PLAYER_BAR_THRESHOLD": {
        "widget": "QSpinBox",
        "tooltip": "The threshold to find the vertical lines inside the region to find the player bar.",
        "min": 100,
        "max": 255
    },
    "DIRT_SATURATION_THRESHOLD": {
        "widget": "QSpinBox",
        "tooltip": "The saturation threshold to find the location of the 'dirt' part.",
        "min": 15,
        "max": 50
    },
    
    "PATHFINDING": {
        "widget": "QCheckBox",
        "tooltip": "Enable or disable pathfinding movement."
    },
    "PATHFINDING_MACRO": {
        "widget": "QComboBox",
        "tooltip": "Select the movement pattern for pathfinding.",
        "items": None
    },
    
    "AUTO_SELL": {
        "widget": "QCheckBox",
        "tooltip": "Enable or disable automatic selling (requires Sell Anywhere gamepass)."
    },
    "AUTO_SELL_REQUIRED_ITEMS": {
        "widget": "QSpinBox",
        "tooltip": "Number of digs before auto-selling will happen.",
        "min": 1,
        "max": 1000
    },
    "AUTO_SELL_BUTTON_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Confidence level for detecting the sell button.",
        "min": 0.35,
        "max": 1.0,
        "step": 0.01
    },
    "AUTO_SELL_AFTER_PATHFINDING_MACRO": {
        "widget": "QCheckBox",
        "tooltip": "This setting will ignore 'AUTO_SELL_REQUIRED_ITEMS' and will sell after the pathfinding macro has finished."
    },

    "USE_PREDICTION": {
        "widget": "QCheckBox",
        "tooltip": "Calculate prediction using acceleration and velocity history."
    },
    "PREDICTION_MAX_TIME_AHEAD": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Used inside the kinematic equation as the variable 't' (bigger = further prediction, but less reliable).",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01
    },
    "PREDICTION_MIN_VELOCITY": {
        "widget": "QSpinBox",
        "tooltip": "Required minimum velocity of the player bar for prediction.",
        "min": 0,
        "max": 1000
    },
    "PREDICTION_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Confidence needed for the prediction to trigger a click (0.0 to 1.0).",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01
    },
    
    "SIDE_CONFIDENCE": {
        "widget": "QDoubleSpinBox",
        "tooltip": "Confidence level for detecting the minigame UI for saving its position (0.0 to 1.0).",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01
    },

    "MOUSE_INPUT_PACKAGE": {
        "widget": "QComboBox",
        "tooltip": "Select the mouse input package to use.",
        "items": mouse_input_packages
    },
    "SCREENSHOT_PACKAGE": {
        "widget": "QComboBox",
        "tooltip": "Select the screenshot package to use.",
        "items": screenshot_packages
    },
    
    "WINDOW_NAME": {
        "widget": "QLineEdit",
        "tooltip": "The name of the UI window."
    },
    "SHOW_DEBUG": {
        "widget": "QCheckBox",
        "tooltip": "Displays a debug image on what the macro sees."
    },
    "DEBUG_FPS": {
        "widget": "QSpinBox",
        "tooltip": "The FPS of the debug image inside the UI window.",
        "min": 1,
        "max": 480,
        "step": 1
    },

    "PREDICTION_SCREENSHOTS": {
        "widget": "QCheckBox",
        "tooltip": "Enables saving prediction screenshots (requires 'Show Debug' to be enabled)."
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

        self.WINDOW_NAME = "DIG Macro by mstudio45"
        self.MSGBOX_ENABLED = True

        self._set_default_config()
        # self.load_config()

    def _set_default_config(self):
        self.default_config = {
            "SYSTEM": {
                "TARGET_FPS": 120,
                "MACOS_DISPLAY_SCALE_OVERRIDE": 0.0,
                "LOGGING_ENABLED": True,
                "MSGBOX_ENABLED": False
            },

            "ROBLOX": {
                "AUTO_REJOIN": False,
                "PRIVATE_SERVER_CODE": "",
                "AUTO_REJOIN_INACTIVITY_TIMEOUT": 1.5,
                "AUTO_REJOIN_CONFIDENCE": 0.85,
                "AUTO_REJOIN_RECONNECT_CONFIDENCE": 0.85
            },

            "MINIGAME": {
                "USE_SAVED_POSITION": True,

                "AUTO_START_MINIGAME": False,
                "MIN_CLICK_INTERVAL": 50,

                "MIN_CENTER_CONFIDENCE": 0.875,
                "MIN_SLOW_CONFIDENCE": 0.7,

                "CLICKABLE_WIDTH": 0.125,
                "PLAYER_BAR_WIDTH": 5,

                "PLAYER_BAR_THRESHOLD": 165 if current_os == "Darwin" else 200,
                "DIRT_SATURATION_THRESHOLD": 22 if current_os == "Darwin" else 50,
            },

            "PATHFINDING": {
                "PATHFINDING": False,
                "PATHFINDING_MACRO": "square",
            },

            "AUTO SELL": {
                "AUTO_SELL": False,
                "AUTO_SELL_REQUIRED_ITEMS": 15,
                "AUTO_SELL_BUTTON_CONFIDENCE": 0.75,
                "AUTO_SELL_AFTER_PATHFINDING_MACRO": False
            },

            "PREDICTION": {
                "USE_PREDICTION": True,
                "PREDICTION_MAX_TIME_AHEAD": 0.05,
                "PREDICTION_MIN_VELOCITY": 300,
                "PREDICTION_CONFIDENCE": 0.8,
            },

            "IMAGE CONFIDENCE": {
                "SIDE_CONFIDENCE": 0.75,
            },

            "PACKAGES": {
                "MOUSE_INPUT_PACKAGE": "Native Calls",
                "SCREENSHOT_PACKAGE": "bettercam" if current_os == "Windows" else "mss",
            },

            "DEBUG WINDOW": {
                "WINDOW_NAME": "DIG Macro by mstudio45",
                "SHOW_DEBUG": True,
                "DEBUG_FPS": 240
            },

            "DEBUG SCREENSHOTS": {
                "PREDICTION_SCREENSHOTS": False,
            },
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
           keys_string = json.dumps(keys)[1:][:-1]
           macro_strings.append(f'    "{name}": [\n        {keys_string}\n    ]')

        macros_content = ",\n".join(macro_strings)
        final_json_string = "{\n" + macros_content + "\n}"

        return final_json_string

    def load_config(self):
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
            
            for key in self.config[section]:
                try:
                    if isinstance(self.config[section][key], bool):
                        value = parser.getboolean(section, key)

                        self.config[section][key] = parser.getboolean(section, key)
                        setattr(self, key,  value)

                    elif isinstance(self.config[section][key], int):
                        value = parser.getint(section, key)

                        self.config[section][key] = parser.getint(section, key)
                        setattr(self, key,  value)

                    elif isinstance(self.config[section][key], float):
                        value = parser.getfloat(section, key)

                        self.config[section][key] = value
                        setattr(self, key,  value)

                    else:
                        value = parser.get(section, key)

                        self.config[section][key] = value
                        setattr(self, key,  value)

                except ValueError:
                    print(f"[ConfigManager.load_config] Warning: Could not parse config value for '[{section}]{key}'. Using default.")

                except configparser.NoOptionError:
                    print(f"[ConfigManager.load_config] Warning: Option '[{section}]{key}' not found in config file. Using default.")
    
        # load PathfindingMacros #
        if os.path.isfile(StaticVariables.pathfinding_macros_filepath):
            try:
                self.PathfindingMacros = json.loads(read(StaticVariables.pathfinding_macros_filepath))
            except json.JSONDecodeError:
                print("[ConfigManager.load_config] Warning: Could not decode 'PathfindingMacros' from config file. Using defaults.")

        return False

    def save_config(self):
        parser = configparser.ConfigParser()
        for section, options in self.config.items():
            parser[section] = {str(k): str(v) for k, v in options.items()}
        
        # save as json #
        write(StaticVariables.pathfinding_macros_filepath, self._format_pathfinding_macros())

        # save as ini #
        with open(self.config_file, 'w') as f:
            parser.write(f)
            f.close()

    # setter #
    def set(self, section, key, value, save_config=True):
        if section in self.config and key in self.config[section]:
            setattr(self, key,  value)
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