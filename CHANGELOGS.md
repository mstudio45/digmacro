# v2.0.2
```diff
[New Features]
+ Added Pausing
+ Added "Gradient" detection method that will be more stable for certain computers
+ Added DIRT_DETECTION, UI_ON_TOP and UI_SCALE_OVERRIDE configurations
+ Added a macOS permission checker for Screen Recording and Accessibility

[Changes]
+ Changed saved region format (OS leftxtop heightxwidth)
+ Added more buttons to the UI (Pause, Configuration, Restart)
+ Removed "Sobel" method since it was slow and unreliable

[Improvements]
+ Better performance
+ Macro loading now waits until Roblox is focused for 1 second before starting
+ Enhanced the minigame recognition system (if it is active or not)
+ Improved prediction screenshot configuration (found and clicked frames are now saved when the setting is enabled)
+ Message boxes now appear above all other windows (Linux and Windows only)
+ Global Hotkeys are now supported on macOS

[Fixes]
+ Fixed Auto Rejoin and Auto Start Minigame
+ Fixed pathfinding on macOS
+ Fixed UI resizing issues on monitors with different resolutions
+ Fixed the version checker
```

# v2.0.1
```diff
[New Features]
+ Added standalone file for Intel CPU MacBooks
+ Added 'Minigame Region' category to configuration GUI
+ Added two algorithms for Player Bar detection
+ Added FPS Counter to UI for computer vision (if it is enabled)

[Improvements]
+ macOS will no longer lock the FPS at 10 when the window is out of focus (except on Sierra)
+ Added more information to the builded binaries properties
+ Added an 'Unsaved Changes' notification to the configuration GUI
+ Refactored certain configuration names and tooltips (you might need to change your config a bit)
+ All empty screenshot folders get deleted on exit

[Fixes]
+ Fixed the macro not working properly on macOS Retina displays
+ Fixed Linux crashing if they don't have required packages installed
+ Fixed the macro crashing when LOGGING_ENABLED is False
+ Fixed shovel re-equipping using the wrong key for certain keyboard layouts
+ Fixed 'Start Macro' and 'Restart' buttons not working properly in compiled binaries
+ Fixed Auto Sell button selector in compiled binaries
```

# v2.0.0
```diff
[New Features]
+ Added 'Auto Rejoin', 'Auto Sell' and 'Auto Start Minigame'
+ Added pathfinding macros
+ Added prediction system
+ Added user based minigame region selection with a guide
+ Added region saving for each different monitor and display resolution into one file
+ Added proper logging system
+ Added configuration GUI and ton of configuration
+ Created standalone binary files compiled with nuitka for each platform for easier user experience

[Improvements]
+ A much more user friendly setup experience 
+ Revamped Macro UI to look better
+ Improved performance (refactored main loop)
+ Adjusted the player bar and dirt part detection

[Fixes]
+ Fixed issues with Windows 11 (works now)
+ Fixed several previous GUI issues with MacOS (tkinter non main thread issues)
```
