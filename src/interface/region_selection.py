import logging
import platform

current_os = platform.system()
__all__ = ["RegionSelector"]

if current_os == "Darwin":
    logging.info("Using 'Darwin' region selector handler...")
    from interface.region_selectors.qt import RegionSelector
else:
    logging.info("Using 'General' region selector handler...")
    from interface.region_selectors.tkinter import RegionSelector