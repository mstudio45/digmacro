import platform
from variables import Variables

current_os = platform.system()
__all__ = ["RegionSelector"]

if current_os == "Darwin":
    import objc # type: ignore
    from Foundation import * # type: ignore
    from AppKit import * # type: ignore
    from Quartz import * # type: ignore

    selected_rect = None

    class RegionSelector_MACOS(NSWindow): # type: ignore
        def init(self):
            screen_frame = NSScreen.mainScreen().frame() # type: ignore
            self = objc.super(RegionSelector_MACOS, self).initWithContentRect_styleMask_backing_defer_(
                screen_frame,
                0, # NSBorderlessWindowMask
                NSBackingStoreBuffered, # type: ignore
                False
            )
            if self:
                self.setLevel_(25)
                self.setOpaque_(False)

                self.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.0, 0.0, 0.0, 0.3)) # type: ignore
                self.setIgnoresMouseEvents_(False)
                self.setAcceptsMouseMovedEvents_(True)
                
                view = RegionSelectorView_MACOS.alloc().initWithFrame_(screen_frame)
                self.setContentView_(view)
                
                self.makeFirstResponder_(view)

            return self

    class RegionSelectorView_MACOS(NSView): # type: ignore
        def initWithFrame_(self, frame):
            self = objc.super(RegionSelectorView_MACOS, self).initWithFrame_(frame)
            if self:
                self.start = None
                self.current = None
                self.selection_rect = None
            return self
        
        def acceptsFirstResponder(self):
            return True
        
        def mouseDown_(self, event):
            point = self.convertPoint_fromView_(event.locationInWindow(), None)
            self.start = point
            self.current = point
            self.setNeedsDisplay_(True)

        def mouseDragged_(self, event): 
            point = self.convertPoint_fromView_(event.locationInWindow(), None)
            self.current = point
            self.setNeedsDisplay_(True)

        def mouseUp_(self, event):
            if self.start and self.current:
                # Calculate selection rectangle
                left = min(self.start.x, self.current.x)
                top = min(self.start.y, self.current.y)
                width = abs(self.current.x - self.start.x)
                height = abs(self.current.y - self.start.y)
                
                screen_height = NSScreen.mainScreen().frame().size.height # type: ignore
                screen_top = screen_height - top - height

                global selected_rect
                selected_rect = {
                    'left': int(left),
                    'top': int(screen_top),
                    'width': int(width),
                    'height': int(height)
                }

            self.window().close()
            NSApp().stop_(self) # type: ignore

        def drawRect_(self, rect):
            NSColor.colorWithRed_green_blue_alpha_(0.0, 0.0, 0.0, 0.3).set() # type: ignore
            NSRectFill(self.bounds()) # type: ignore
            
            if self.start and self.current:
                selection_rect = NSMakeRect( # type: ignore
                    min(self.start.x, self.current.x),
                    min(self.start.y, self.current.y),
                    abs(self.current.x - self.start.x),
                    abs(self.current.y - self.start.y)
                )
                
                NSColor.colorWithRed_green_blue_alpha_(0.0, 1.0, 0.0, 0.2).set() # type: ignore
                NSRectFill(selection_rect) # type: ignore

                path = NSBezierPath.bezierPathWithRect_(selection_rect) # type: ignore
                NSColor.colorWithRed_green_blue_alpha_(0.0, 1.0, 0.0, 1.0).set() # type: ignore
                path.setLineWidth_(2)
                path.stroke()
        
        def keyDown_(self, event):
            if event.keyCode() == 53: # escape key #
                global selected_rect
                selected_rect = None

                self.window().close()
                NSApp().stop_(self) # type: ignore

    class RegionSelector:
        def __init__(self):
            pass

        def start(self):
            app = NSApplication.sharedApplication() # type: ignore
            window = RegionSelector_MACOS.alloc().init()
            window.makeKeyAndOrderFront_(None)
            app.run()

        def get_selection(self):
            return selected_rect
else:
    import tkinter as tk

    class RegionSelector:
        def __init__(self):
            pass

        def start(self):
            self.root = tk.Tk()
            
            # overlay over the screen (fullscren borderless) #
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            
            # add bg #
            if current_os == "Linux":
                self.root.wait_visibility(self.root)
                self.root.wm_attributes("-alpha", 0.3) 
                self.root.configure(bg="black")
                self.root.wm_attributes("-topmost", True)
            else:
                self.root.overrideredirect(True)
                self.root.attributes("-alpha", 0.3) 
                self.root.configure(bg="black")
                self.root.attributes("-topmost", True)
                
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
            self.root.destroy()

        def on_escape(self, event):
            self.selection = None
            Variables.is_running = False
            self.root.destroy()

        def get_selection(self):
            return self.selection