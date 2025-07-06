import sys, traceback
import numpy as np
import logging
import cv2, base64, io
from PIL import Image
import platform, mss

current_os = platform.system()
import interface.msgbox as msgbox

from config import Config
from utils.images.screenshots import take_screenshot

__all__ = [
    "resize_image", "stack_images_with_dividers", "find_image", "write_image",
    
    "screen_region", "screen_res_str",
    "scale_x", "scale_y", "scale_factor"
]

# get the display resolution to support all window sizes #
BASE_RESOLUTION = (1920, 1080)
screen_res_str = "0x0 1920x1080"
scale_x, scale_y, scale_factor = 1.0, 1.0, 1.0
base_width, base_height = BASE_RESOLUTION
screen_region = { "left": 0, "top": 0, "width": BASE_RESOLUTION[0], "height": BASE_RESOLUTION[1] }
logical_screen_region = { "left": 0, "top": 0, "width": BASE_RESOLUTION[0], "height": BASE_RESOLUTION[1] }

# calculate valid display resolutions (physical) and get scale_factor #
class FailedToGetDiplayResolutionException(Exception): ...
try:
    if current_os == "Darwin":
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
                    msgbox.alert(f"Could not retrieve macOS display info via fallback: {str(e)}", bypass=True)
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
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
            logging.info("SetProcessDpiAwarenessContext to PER_MONITOR_AWARE_V2")
        except AttributeError: # fallback for older win versions
            try:
                ctypes.windll.user32.SetProcessDPIAware()
                logging.info("SetProcessDPIAware to System Aware")
            except Exception as e:
                msgbox.alert(f"Could not set DPI awareness: {e}", log_level=logging.ERROR, bypass=True)

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

                    "scale_factor": min(scale_factor_x, scale_factor_y),
                    "system_dpi": system_dpi
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
except FailedToGetDiplayResolutionException as e:
    msgbox.alert(f"Failed to get the correct Display Resolution: {str(e)}")
    sys.exit(1)
except Exception as e:
    msgbox.alert(f"Failed to get the correct Display Resolution: {traceback.format_exc()}")
    sys.exit(1)

logging.info(f"\nPhysical Screen region (scaled by DPI):\n    {screen_region} | {scale_x:.2f}x{scale_y:.2f} - {scale_factor}\nBase Resolution:\n    {BASE_RESOLUTION} | 1x1 1")

def resize_image(img_path):
    global scale_factor

    try:
        # read the image without changes #
        image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if image is None: raise IOError(f"Image not found at {str(img_path)}")

        # calculate new resize dimensions #
        h, w, _ = image.shape
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    except Exception as e:
        msgbox.alert(f"Failed to resize the image '{str(img_path)}': \n{traceback.format_exc()}")
        sys.exit(1)

def stack_images_with_dividers(images, margin_thickness=2):
    lenght_images = len(images)
    if lenght_images == 0: return None
    if lenght_images == 1: return images[0]

    try:
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
    
def find_image(image, confidence, log=False, region=None):
    if region == None:
        if current_os == "Windows" and Config.SCREENSHOT_PACKAGE == "bettercam (Windows)":
            region = logical_screen_region
        else:
            region = screen_region
    
    try:
        sct = mss.mss()
        screenshot_bgr = take_screenshot(region, sct)

        template = cv2.imread(image, cv2.IMREAD_COLOR) if isinstance(image, str) else image
        if template is None:
            try: sct.close() 
            except: pass

            logging.error("Image is None.")
            return None
        
        # ensure same format and number of dimensions #
        if len(screenshot_bgr.shape) != len(template.shape):
            try: sct.close() 
            except: pass

            logging.error("Screenshot and template have different number of dimensions.")
            return None

        if screenshot_bgr.shape[2] != template.shape[2]:
            if screenshot_bgr.shape[2] == 4: screenshot_bgr = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGRA2BGR)
            if template.shape[2] == 4: template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)

        # get shapes #
        h_template, w_template = template.shape[:2]
        h_screen, w_screen = screenshot_bgr.shape[:2]

        # template (img we want to find) is bigger than screenshot #
        if h_template > h_screen or w_template > w_screen:
            try: sct.close() 
            except: pass

            logging.error("Image is bigger than screenshot.")
            return None
        
        # match the template #
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if log == True: print(f"Max: {max_val} >= {confidence}")
        if max_val >= confidence:
            try: sct.close() 
            except: pass
            
            top_left = max_loc
            return { "left": top_left[0], "top": top_left[1], "width": w_template, "height": h_template }
        
        return None
    except Exception as e:
        logging.error(f"Error: \n{traceback.format_exc()}")
    
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
