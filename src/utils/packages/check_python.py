import sys
import subprocess
import os

import importlib
import importlib.util

from utils.packages.distro_variables import log_install, current_os, install_pip_package
from utils.packages.versions import is_version_outdated, is_version_over_required

__all__ = ["check_pip_packages"]
required_packages = {
    "all": [
        { "pip": "opencv-python-headless", "import": "cv2",            "version": "all"   },
        { "pip": "PyScreeze",              "import": "pyscreeze",      "version": "all"   },                
        { "pip": "mss",                    "import": "mss",            "version": "all"   },
        { "pip": "screeninfo",             "import": "screeninfo",     "version": "all"   },
        { "pip": "requests",               "import": "requests",       "version": "all"   },
        { "pip": "PySide6",                "import": "PySide6",        "version": "all"   },
        { "pip": "psutil",                 "import": "psutil",         "version": "all"   },
        { "pip": "pillow",                 "import": "PIL",            "version": "all"   },
        { "pip": "watchdog",               "import": "watchdog",       "version": "all"   },
        { "pip": "nextcord",               "import": "nextcord",       "version": "all"   },

        { "pip": "pandas",                 "import": "pandas",         "version": "all"   },
        { "pip": "matplotlib",             "import": "matplotlib",     "version": "all"   },

        # { "pip": "transformers",         "import": "transformers",   "version": "all"   },
        { "pip": "scikit-image",           "import": "skimage",        "version": "all"   },
        { "pip": "easyocr",                "import": "easyocr",        "version": "all"   },
        { "pip": "torch",                  "import": "torch",          "version": "all"   },
        { "pip": "torchvision",            "import": "torchvision",    "version": "all"   },
        # { "pip": "torchaudio",           "import": "torchaudio",     "version": "all"   },

        { "pip": "pynput",                 "import": "pynput",         "version": "1.8.1" },
        { "pip": "numpy",                  "import": "numpy",          "version": "2.2.6" },
    ],

    "Windows": [
        { "pip": "pywebview",              "import": "webview",        "version": "all"   },
        { "pip": "bettercam",              "import": "bettercam",      "version": "all"   },
        { "pip": "comtypes",               "import": "comtypes",       "version": "all"   },
        { "pip": "PyGetWindow",            "import": "pygetwindow",    "version": "all"   },
        { "pip": "pywin32",                "import": "win32gui",       "version": "all"   },
        { "pip": "PyAutoIt",               "import": "autoit",         "version": "all"   },
    ],

    "Linux": [
        { "pip": "pywebview[gtk]",         "import": "webview",       "version": "all"   },
    ],

    "Darwin": [
        { "pip": "pywebview",              "import": "webview",       "version": "all"   },
        { "pip": "pyobjc",                 "import": "AppKit",        "version": "all"   },
    ]
}
check_import_only = ["pywebview[gtk]"]
binary_only = ["opencv-python-headless", "numpy", "matplotlib", "torch", "torchvision", "torchaudio"]
skip_binary_check = ["opencv-python-headless"]
no_depends = ["bettercam", "easyocr"]

if current_os not in required_packages: 
    def check_pip_packages(): 
        log_install("[check_pip_packages] There are no packages to install for this OS.")
        return False

else:
    def get_parent_dirs(path):
        parents = []
        path = os.path.abspath(path)

        while True:
            path, tail = os.path.split(path)
            if not tail: break
            parents.append(path)
        return parents

    def is_binary_install(package_name):
        try:
            spec = importlib.util.find_spec(package_name)
            if spec is None or spec.origin is None:
                return None
            
            package_path = os.path.abspath(spec.origin)
            base_dir = os.path.dirname(package_path)

            # check .egg-info or .dist-info #
            parent_dirs = get_parent_dirs(base_dir)
            package_pattern = package_name.replace("-", "_")

            for d in parent_dirs:
                try: entries = os.listdir(d)
                except FileNotFoundError: continue
                
                dist_infos = []
                egg_infos = []

                for entry in entries:
                    if entry.startswith(package_pattern) and entry.endswith('.dist-info'):
                        dist_infos.append(os.path.join(d, entry))
                    elif entry.startswith(package_pattern) and entry.endswith('.egg-info'):
                        egg_infos.append(os.path.join(d, entry))
                
                if len(dist_infos) > 0: return True # likely a binary wheel #
                elif len(egg_infos) > 0: return False # likely a source install or editable install #

            return False # no information #
        except Exception as e:
            log_install(f"[is_binary_install] Error checking if '{package_name}' is binary: {str(e)}")
            return None

    def check_pip_packages():
        compiled = "__compiled__" in globals()
        if compiled: 
            log_install("[check_pip_packages] Compiled mode, skipping...")
            return False

        freeze_list = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        installed_packages = [r.decode().split("==") for r in freeze_list.split()]

        # get relevant packages #
        relevant_packages = required_packages.get("all", []) + required_packages.get(current_os, [])

        log_install(f"[check_pip_packages] Checking missing packages (packages['all'] + packages['{current_os}'])...")

        # get missing packages #
        missing_packages = []

        if "--force-reinstall" in sys.argv:
            missing_packages = relevant_packages
            log_install("Reinstalling packages...")
        else:
            total = len(relevant_packages)
            idx = 0
            for package in relevant_packages:
                pip_name = package["pip"]
                import_name = package["import"]
                min_version = package["version"]
                idx = idx + 1

                log_install(f"[check_pip_packages] Checking '{pip_name}' ({idx}/{total})")

                # check pip freeze list #
                if pip_name not in check_import_only:
                    installed_package = next((item for item in installed_packages if item[0] == pip_name), None)
                    if installed_package is None:
                        log_install(f"[check_pip_packages] Package '{pip_name}' is not installed.")
                        missing_packages.append(package)
                        continue
                    
                    if min_version != "all":
                        if is_version_outdated(installed_package[1], min_version):
                            log_install(f"[check_pip_packages] Package '{pip_name}' is too old: {installed_package[1]} < {min_version}")
                            missing_packages.append(package)
                            continue

                        elif is_version_over_required(installed_package[1], min_version):
                            log_install(f"[check_pip_packages] Package '{pip_name}' is over the required version: {installed_package[1]} > {min_version}")
                            missing_packages.append(package)
                            continue
                
                # check import #
                try: importlib.import_module(import_name)
                except ImportError as e: 
                    log_install(f"[check_pip_packages] Package '{pip_name}' didn't import properly: {str(e)}")
                    missing_packages.append(package)

                # check binary install #
                if pip_name in binary_only and pip_name not in skip_binary_check:
                    is_binary = is_binary_install(import_name)
                    if is_binary == False:
                        log_install(f"[check_pip_packages] Package '{pip_name}' is not a binary install.")
                        missing_packages.append(package)
                    elif is_binary == None:
                        log_install(f"[check_pip_packages] Package '{pip_name}' could not be check: is_binary_install returned None")

        # install packages #
        if len(missing_packages) == 0:
            log_install("[check_pip_packages] All required packages are installed.\n")
            return False

        log_install(f"[check_pip_packages] Missing packages detected: {missing_packages}")
        for package in missing_packages: 
            install_pip_package(package, only_binary=package["pip"] in binary_only, no_deps=package["pip"] in no_depends)
        
        log_install("[check_pip_packages] Done.\n")
        return True