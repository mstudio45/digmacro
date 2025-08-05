import platform
from config import Config

current_os = platform.system()

__all__ = ["MainHandler"]
if current_os == "Windows" and Config.GLOBAL_DETECTION_METHOD == "Memory":
    from utils.detectors.minigame.memory.handler import MainHandler
else:
    from utils.detectors.minigame.opencv.handler import MainHandler