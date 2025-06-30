import sys, traceback
import numpy as np
import cv2, pymsgbox, pyautogui

BASE_RESOLUTION = (1920, 1080)
__all__ = [
    "resize_image", "stack_images_with_dividers", "find_image", "write_image",
    "current_screen_width", "current_screen_height",
    "scale_x", "scale_y", "scale_factor"
]

# get the display resolution to support all window sizes #
try:
    current_screen_width, current_screen_height = pyautogui.size()
    base_width, base_height = BASE_RESOLUTION

    scale_x = current_screen_width / base_width
    scale_y = current_screen_height / base_height
    scale_factor = (scale_x + scale_y) / 2.0
except:
    pymsgbox.alert("Failed to get the current Display Resolution, please setup pyautogui correctly.")
    sys.exit(1)

from utils.general.screenshots import take_screenshot

def resize_image(img_path):
    global scale_factor

    try:
        # read the image without changes #
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise IOError(f"[OpenCV_Resizer.resize_img] Image not found at {str(img_path)}")

        # calculate new resize dimensions #
        h, w, _ = img.shape
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)

        # resize the image using INTER_AREA #
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    except Exception as e:
        pymsgbox.alert(f"[OpenCV_Resizer.resize_img] Failed to resize the image '{str(img_path)}': \n{traceback.format_exc()}")
        sys.exit(1)

def stack_images_with_dividers(images, margin_thickness=2):
    if len(images) == 0:
        return None

    try:
        target_width = images[0].shape[1]
        max_height = 0
        for img in images:
            h, w = img.shape[:2]
            scaled_h = int(target_width * (h / w))
            if scaled_h > max_height:
                max_height = scaled_h

        # resize images #
        resized_and_padded_images = []
        for img in images:
            h, w = img.shape[:2]

            # convert to bgr #
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif img.shape[2] == 1: 
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            # get height #
            aspect_ratio = h / w
            new_height = int(target_width * aspect_ratio)

            if (new_height, target_width) != (h, w): 
                img_resized = cv2.resize(img, (target_width, new_height), interpolation=cv2.INTER_AREA)
            else:
                img_resized = img 

            # resize by width and dont stretch height #
            canvas = np.full((max_height, target_width, 3), (0, 0, 0), dtype=np.uint8)
            y_offset = (max_height - new_height) // 2
            canvas[y_offset : y_offset + new_height, 0:target_width] = img_resized
            
            resized_and_padded_images.append(canvas)

        # add dividers #
        full_divider_height = (2 * margin_thickness)
        full_divider = np.full((full_divider_height, target_width, 3), (0, 0, 0), dtype=np.uint8)

        # stack together #
        stacked = resized_and_padded_images[0]
        for img in resized_and_padded_images[1:]:
            stacked = np.concatenate((stacked, full_divider, img), axis=0)

        return stacked
    except Exception as e:
        print(f"[stack_images_with_dividers] Failed to stack images: \n{traceback.format_exc()}")
        return None
    
def find_image(image, confidence, custom_sct=None, log=False, region={"left": 0, "top": 0, "width": base_width, "height": base_height}):
    try:
        screenshot_bgr = take_screenshot(region=region, custom_sct=custom_sct)

        template = cv2.imread(image, cv2.IMREAD_COLOR) if isinstance(image, str) else image
        if template is None:
            pymsgbox.alert(f"[find_image] Image is None.")
            return None

        # get shapes #
        h_template, w_template = template.shape[:2]
        h_screen, w_screen = screenshot_bgr.shape[:2]

        # template (img we want to find) is bigger than screenshot #
        if h_template > h_screen or w_template > w_screen:
            pymsgbox.alert(f"[find_image] Image is bigger than screenshot.")
            return None
        
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if log == True:
            print(f"Max: {max_val} >= {confidence}")
        
        if max_val >= confidence:
            top_left = max_loc
            return { "left": top_left[0], "top": top_left[1], "width": w_template, "height": h_template }
        
        return None
    except Exception as e:
        pymsgbox.alert(f"[find_image] Error: \n{traceback.format_exc()}")
    
    return None

def write_image(filepath, image):
    try: cv2.imwrite(filename=filepath, img=image)
    except Exception as e:
        print(f"[write_image] '{str(filepath)}' write error: \n{traceback.format_exc()} ")