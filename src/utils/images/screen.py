import sys, traceback, logging, platform
import base64, io
from PIL import Image

import numpy as np
import cv2

current_os = platform.system()
import interface.msgbox as msgbox
from config import Config

__all__ = [
    "stack_images_with_dividers", "write_image",
    
    "screen_region", "logical_screen_region", "screen_res_str",
    "scale_x", "scale_y", "scale_factor",
    "scale_x_1080p", "scale_y_1080p"
]

# get the display resolution to support all window sizes #
BASE_RESOLUTION = (1920, 1080)
screen_res_str = "0x0 1920x1080"
base_width, base_height = BASE_RESOLUTION

scale_x, scale_y, scale_factor = 1.0, 1.0, 1.0
screen_region = { "left": 0, "top": 0, "width": BASE_RESOLUTION[0], "height": BASE_RESOLUTION[1] }
logical_screen_region = { "left": 0, "top": 0, "width": BASE_RESOLUTION[0], "height": BASE_RESOLUTION[1] }

# calculate valid display resolutions (physical) and get scale_factor #
class FailedToGetDiplayResolutionException(Exception): ...
try:
    if current_os == "Darwin":
        logging.info("Using 'PyObjC' to get monitor information...\n")

        import objc, subprocess # type: ignore
        from AppKit import NSScreen # type: ignore

        def get_macos_display_info():
            try:
                main_screen = NSScreen.mainScreen()
                if main_screen:
                    backing_scale = main_screen.backingScaleFactor()
                    logical_frame = main_screen.frame()
                    
                    logical_width = int(logical_frame.size.width)
                    logical_height = int(logical_frame.size.height)
                    
                    physical_width = int(logical_width * backing_scale)
                    physical_height = int(logical_height * backing_scale)
                    
                    monitor_left = int(logical_frame.origin.x)
                    monitor_top = int(logical_frame.origin.y)

                    return {
                        "left": monitor_left,
                        "top": monitor_top,

                        "logical_width": logical_width,
                        "logical_height": logical_height,

                        "physical_width": physical_width,
                        "physical_height": physical_height,

                        "scale_factor": float(backing_scale)
                    }
            except Exception as e:
                try:
                    result = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True, timeout=10)
                    output = result.stdout
                    
                    scale_factor = 2.0 if "Retina" in output or "5K" in output or "4K" in output else 1.0
                    for line in output.splitlines():
                        if "Resolution:" in line:
                            parts = line.split()
                            try:
                                width_index = parts.index("x") - 1
                                height_index = parts.index("x") + 1

                                physical_width = int(parts[width_index])
                                physical_height = int(parts[height_index])
                                
                                logical_width = int(physical_width / scale_factor)
                                logical_height = int(physical_height / scale_factor)
                                
                                return {
                                    "left": 0,
                                    "top": 0,

                                    "logical_width": logical_width,
                                    "logical_height": logical_height,

                                    "physical_width": physical_width,
                                    "physical_height": physical_height,

                                    "scale_factor": scale_factor
                                }
                            except (ValueError, IndexError):
                                continue # invalid format
                                
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                    msgbox.alert(f"Could not retrieve macOS display info via fallback: {str(e)}")
            return None
        
        macos_screen_info = get_macos_display_info()
        if not macos_screen_info: raise FailedToGetDiplayResolutionException("Failed to get macOS display information.")

        # custom scale override #
        override_scale = Config.MACOS_DISPLAY_SCALE_OVERRIDE
        if override_scale > 0.0:
            logical_width = macos_screen_info["logical_width"]
            logical_height = macos_screen_info["logical_height"]

            macos_screen_info = {
                "left": macos_screen_info["left"],
                "top": macos_screen_info["top"],

                "logical_width": logical_width,
                "logical_height": logical_height,

                "physical_width": int(logical_width * override_scale),
                "physical_height": int(logical_height * override_scale),

                "scale_factor": override_scale
            }

        # set variables #
        screen_region = {
            "left": macos_screen_info["left"],
            "top": macos_screen_info["top"],
            "width": macos_screen_info["physical_width"], 
            "height": macos_screen_info["physical_height"]
        }
        logical_screen_region = {
            "left": macos_screen_info["left"],
            "top": macos_screen_info["top"],
            "width": macos_screen_info["logical_width"], 
            "height": macos_screen_info["logical_height"]
        }

    elif current_os == "Windows":
        logging.info("Using 'ctypes' to get monitor information...\n")

        import ctypes, ctypes.wintypes
        
        MDT_EFFECTIVE_DPI = 0

        def get_windows_display_info():
            try:
                hmonitor = ctypes.windll.user32.MonitorFromPoint(ctypes.wintypes.POINT(0, 0), MDT_EFFECTIVE_DPI)
                if not hmonitor: raise FailedToGetDiplayResolutionException("Could not get primary monitor handle for Windows DPI info.")

                dpi_x = ctypes.c_uint()
                dpi_y = ctypes.c_uint()
                ctypes.windll.shcore.GetDpiForMonitor(hmonitor, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y))

                system_dpi = 96.0 
                scale_factor_x = dpi_x.value / system_dpi
                scale_factor_y = dpi_y.value / system_dpi

                logical_width = ctypes.windll.user32.GetSystemMetrics(0) # SM_CXSCREEN #
                logical_height = ctypes.windll.user32.GetSystemMetrics(1) # SM_CYSCREEN #

                physical_width = int(logical_width * scale_factor_x)
                physical_height = int(logical_height * scale_factor_y)

                # get left, top #
                class MONITORINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.wintypes.DWORD),
                        ("rcMonitor", ctypes.wintypes.RECT),
                        ("rcWork", ctypes.wintypes.RECT),
                        ("dwFlags", ctypes.wintypes.DWORD),
                    ]

                monitor_info = MONITORINFO()
                monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
                ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(monitor_info))

                monitor_left = monitor_info.rcMonitor.left
                monitor_top = monitor_info.rcMonitor.top

                return {
                    "left": monitor_left,
                    "top": monitor_top,

                    "logical_width": logical_width,
                    "logical_height": logical_height,

                    "physical_width": physical_width,
                    "physical_height": physical_height,

                    "scale_factor": min(scale_factor_x, scale_factor_y)
                }
            except Exception as e:
                logging.error(f"Error getting Windows DPI info: {e}")
                return None
        
        windows_screen_info = get_windows_display_info()
        if not windows_screen_info: raise FailedToGetDiplayResolutionException("Failed to get windows display information.")

        screen_region = {
            "left": windows_screen_info["left"],
            "top": windows_screen_info["top"],
            "width": windows_screen_info["physical_width"], 
            "height": windows_screen_info["physical_height"]
        }
        logical_screen_region = {
            "left": windows_screen_info["left"],
            "top": windows_screen_info["top"],
            "width": windows_screen_info["logical_width"], 
            "height": windows_screen_info["logical_height"]
        }

    elif current_os == "Linux":
        logging.info("Using 'screeninfo' to get monitor information...\n")

        from screeninfo import get_monitors
        monitors = get_monitors()

        primary_monitor = next((m for m in monitors if m.is_primary), monitors[0] if monitors else None)
        if not primary_monitor: raise FailedToGetDiplayResolutionException("Could not find any monitors with the 'screeninfo' library.")

        screen_region = {
            "left": primary_monitor.x,
            "top": primary_monitor.y,
            "width": primary_monitor.width,
            "height": primary_monitor.height
        }
        logical_screen_region = {
            "left": primary_monitor.x,
            "top": primary_monitor.y,
            "width": primary_monitor.width,
            "height": primary_monitor.height
        }
        
    # make scale_factor #
    screen_res_str = f"{screen_region["left"]}x{screen_region["top"]} {screen_region["width"]}x{screen_region["height"]}"

    scale_x = screen_region["width"] / base_width
    scale_y = screen_region["height"] / base_height
    scale_factor = min(scale_x, scale_y) # aspect ratio #

    scale_x_1080p, scale_y_1080p = 1920 / screen_region["width"], 1080 / screen_region["height"]
except FailedToGetDiplayResolutionException as e:
    msgbox.alert(f"Failed to get the correct Display Resolution: {str(e)}")
    sys.exit(1)
except Exception as e:
    msgbox.alert(f"Failed to get the correct Display Resolution: {traceback.format_exc()}")
    sys.exit(1)

# DEBUG INFO
logging.info(f"=== SCALING DEBUG INFO ===")

# res #
logging.info(f"Base Resolution (resolution that was used for asset images): {BASE_RESOLUTION}")
logging.info(f"Screen Resolution: {screen_res_str}")
logging.info(f"Current (Physical) Screen Region: {screen_region}")
logging.info(f"Logical Screen Region: {logical_screen_region}\n")

# scale #
logging.info(f"Scale X: {scale_x:.5f}, Scale Y: {scale_y:.5f}")
logging.info(f"Scale Factor: {scale_factor:.5f}")
logging.info(f"Image Finder Scale Factor: {1.0 / scale_factor:.5f}")
logging.info(f"Scale factor (to 1080p): {scale_x_1080p}, {scale_y_1080p}\n")

logging.info(f"Screenshot package: {Config.SCREENSHOT_PACKAGE}")
logging.info(f"========================\n")

black_pixel = np.zeros((1, 1, 3), dtype=np.uint8)
def stack_images_with_dividers(images, margin_thickness=2):
    lenght_images = len(images)
    if lenght_images == 0: return None
    if lenght_images == 1: return images[0]

    try:
        idx = 0
        for image in images:
            if image is None: images[idx] = black_pixel.copy()
            idx = idx + 1
        
        max_width = max(img.shape[1] for img in images)
        max_height = max(img.shape[0] for img in images)

        # resize images #
        resized_and_padded_images = []
        for image in images:
            h, w = image.shape[:2]

            # convert to bgr #
            if image.ndim == 2 or image.shape[2] == 1:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

            # get height #
            scale = min(max_width / w, max_height / h)
            new_w = int(w * scale)
            new_h = int(h * scale)

            image_resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # resize by width and dont stretch height #
            canvas = np.full((max_height, max_width, 3), (0, 0, 0), dtype=np.uint8)
            y_offset = (max_height - new_h) // 2
            x_offset = (max_width - new_w) // 2
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = image_resized
            
            resized_and_padded_images.append(canvas)

        # add dividers #
        full_divider = np.full((2 * margin_thickness, max_width, 3), (0, 0, 0), dtype=np.uint8)

        # stack together #
        stacked = resized_and_padded_images[0]
        for img in resized_and_padded_images[1:]:
            stacked = np.concatenate((stacked, full_divider, img), axis=0)

        return stacked
    except Exception as e:
        logging.error(f"Failed to stack images: \n{traceback.format_exc()}")
        return None

def write_image(filename, image):
    try: 
        if image.ndim == 2 or image.shape[2] == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.imwrite(filename, image)
    except Exception as e:
        logging.error(f"'{str(filename)}' write error: \n{traceback.format_exc()}")

def image_to_base64(image):
    try:
        if image.ndim == 2 or image.shape[2] == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(image)

        # to base64 #
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except: return ""