from config import Config

__all__ = ["take_screenshot", "cleanup"]

if Config.SCREENSHOT_PACKAGE == "win32api":
    import win32gui, win32ui, win32con
    import numpy as np

    # get desktop variables #
    hwnd = win32gui.GetDesktopWindow()
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()

    def take_screenshot(region, _invalid_arg_for_win32 = None):
        x, y, w, h = region["left"], region["top"], region["width"], region["height"]

        # create bitmap #
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
        cDC.SelectObject(dataBitMap)

        # copy to bitmap #
        cDC.BitBlt((0,0), (w, h), dcObj, (x, y), win32con.SRCCOPY)

        # raw bytes from bitmap #
        bits = dataBitMap.GetBitmapBits(True)
        bmp_info = dataBitMap.GetInfo()

        # GetBitmapBits(True) #
        img_np = np.frombuffer(bits, dtype=np.uint8).copy() # .copy so its write and read
        img_np = bits.reshape((bmp_info["bmHeight"], bmp_info["bmWidth"], 4))
        img_np = img_np[..., :3][..., ::-1] # to bgr


        # delete bitmap and return #
        win32gui.DeleteObject(dataBitMap.GetHandle())
        return img_np

    def cleanup():
        print("[screenshots.cleanup] Cleaning...")

        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
else:
    import numpy as np
    import mss

    sct = mss.mss()
    def take_screenshot(region, custom_sct = None):
        return np.array((custom_sct or sct).grab(region), dtype=np.uint8)
    
    def cleanup():
        print("[screenshots.cleanup] Cleaning...")