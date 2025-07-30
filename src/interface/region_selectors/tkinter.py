import platform

from utils.images.screen import screen_region
from variables import Variables

import tkinter as tk

current_os = platform.system()
__all__ = ["RegionSelector"]

class RegionSelector:
    def __init__(self, stop_macro=False):
        self.stop_macro = stop_macro
        self.stopped = False

    def start(self):
        self.root = tk.Tk()
        
        # overlay over the screen (fullscren borderless) #
        self.root.geometry(f"{screen_region["width"]}x{screen_region["height"]}+{screen_region["left"]}+{screen_region["top"]}")
        
        # add bg #
        if current_os == "Linux": self.root.wait_visibility(self.root)
        else: self.root.overrideredirect(True)
        
        self.root.wm_attributes("-alpha", 0.3) 
        self.root.configure(bg="black")
        self.root.wm_attributes("-topmost", True)
            
        # make canvas #
        self.canvas = tk.Canvas(self.root, cursor="cross", highlightthickness=0, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = self.start_y = 0
        self.rect = None
        self.selection = None

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        self.root.bind("<Escape>", self.on_escape)
        self.root.focus_set()
        self.root.mainloop()

    def stop(self):
        if self.stopped: return
        self.stopped = True
        
        try:
            if self.stop_macro == True: Variables.is_running = False
            self.root.destroy()
        except: pass

    def get_selection(self):
        return self.selection

    #######################################################################################

    def on_mouse_press(self, event):
        self.start_x, self.start_y = event.x_root, event.y_root
        x = event.x_root - self.root.winfo_rootx()
        y = event.y_root - self.root.winfo_rooty()

        self.rect = self.canvas.create_rectangle(
            x, y, x, y,
            outline="#00FF00",
            width=2,
            fill="#00FF00",
            stipple="gray25"
        )

    def on_mouse_drag(self, event):
        x = event.x_root - self.root.winfo_rootx()
        y = event.y_root - self.root.winfo_rooty()

        start_x_local = self.start_x - self.root.winfo_rootx()
        start_y_local = self.start_y - self.root.winfo_rooty()

        self.canvas.coords(self.rect, start_x_local, start_y_local, x, y)

    def on_mouse_release(self, event):
        end_x, end_y = event.x_root, event.y_root

        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        self.selection = {
            "left": x1,
            "top": y1,
            "width": x2 - x1,
            "height": y2 - y1,
        }
        self.root.destroy() # use destroy so the macro doesnt exit with stop_macro = true #

    def on_escape(self, event):
        self.selection = None
        self.stop()