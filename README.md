# DIG macro
<p align="center">
  <img width="60%" src="assets/showcase.gif" alt="Showcase video"> <br />
  Auto minigame macro for [DIG](https://www.roblox.com/games/126244816328678/DIG). 
</p>

> [!NOTE]
> Do not expect this macro to succeed every time it attempts to dig.

> [!WARNING]
> **This macro can missclick and end your streak!** It may also fail frequently in specific situations (such as with snow).

## Requirements
 * [Python](https://www.python.org/) **[Recommended version: 3.13]**
 * [wmctrl](https://github.com/saravanabalagi/wmctrl) **[Only for Linux users]**
    - On Debian/Ubuntu: `sudo apt-get install wmctrl`
    - On Fedora: `sudo dnf install wmctrl`

## Installation
1.  **Clone or Download:**
    ```bash
    git clone https://github.com/mstudio45/digmacro
    cd digmacro
    ```
    
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run
1.  **Change the in-game settings:**
    * `Minigame Dimming`: **1**

2.  **Change the monitor settings:**
    * `Resolution`: **1920x1080 (16:9)**

3.  **Run the Script:**
    ```bash
    py main.py
    ```
## How to Stop
  * Simply **close the "debug" window**.
  * Alternatively, you can press `Ctrl+C` in the terminal where the script is running.

## Configuration
You can tweak the script's behavior by modifying the settings at the top of the `main.py` file.
| Variable                            | Description                                                                                                         |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `CLICKABLE_WIDTH`                   | Width of the "STRONG" clicking area.                                                                                
| `CHECK_FOR_BLACK_SCREEN`            | Set to `False` to disable the background dimming check (**this will cause a lot of random left clicks**).               
| `WINDOW_NAME`                       | Title of the Debug Window.                                                                                          
| `SHOW_DEBUG`                        | Set to `False` to disable the debug window for a slight performance gain (it will open an window with no image instead so you can easily stop the macro).
| `MIN_BAR_HEIGHT` / `MAX_BAR_HEIGHT` | Detection variables of the bar UI. (experimental)
| `INTENSITY_DIFF_THRESHOLD`          | Sensitivity for detecting the top and bottom of the bar UI. (experimental)
