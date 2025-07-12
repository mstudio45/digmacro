import sys, subprocess, traceback
from utils.packages.distro_variables import *

__all__ = ["check_apt_packages"]
required_packages = {
    "Linux": {
        "all": {
            "gcc": "gcc",
        },

        "ubuntu_based": {
            "libgirepository1.0-dev": "libgirepository1.0-dev", 
            "libgirepository-2.0-dev": "libgirepository-2.0-dev",
            "libgtk-3-0t64": "libgtk-3-0"
        },

        "rhel_based": {
            "gobject-introspection-devel": "gobject-introspection-devel",
            "gtk3": "gtk3",
            "python3-gobject": "python3-gobject"
        },

        "arch_based": {
            "gobject-introspection": "gobject-introspection",
            "gtk3": "gtk3"
        },

        "opensuse_based": {
            "gobject-introspection-devel": "gobject-introspection-devel",
            "gtk3-devel": "gtk3-devel"
        }
    }
}

if current_os not in required_packages: 
    def check_apt_packages(): 
        print("[check_apt_packages] There are no packages to install for this OS.")
        return False
else:
    installed_packages = get_linux_installed_packages()
    if isinstance(installed_packages, str):
        print(installed_packages)
        sys.exit(1)

    # get relevant packages #
    os_required = required_packages[current_os] 
    relevant_packages = list(os_required.get("all", {}).items()) + list(os_required.get(distro_key, {}).items())

    def check_apt_packages():
        print(f"[check_apt_packages] Checking missing packages ({current_os}['all'] + {current_os}['{distro_key}'])...")

        # get missing packages #
        missing_packages = []
        for check_first, install_name in relevant_packages:
            if check_first in installed_packages: continue
            if install_name in installed_packages: continue

            missing_packages.append(install_name)

        if len(missing_packages) == 0: 
            print("[check_apt_packages] All required system packages are installed.\n")
            return False
        
        # get install command #
        base_install_cmd = []
        if current_os == "Linux":
            base_install_cmd = get_linux_app_install_cmd()
            if isinstance(base_install_cmd, str):
                print(base_install_cmd)
                sys.exit(1)

        # install packages #
        for missing_package in missing_packages:
            try:
                install_cmd = base_install_cmd + [missing_package]
                print(f"[check_apt_packages] Installing system package: {missing_package} using {install_cmd}")
                subprocess.check_call(install_cmd)
            except Exception as e:
                print(f"[check_apt_packages] Failed to install '{missing_package}' requirement: \n{traceback.format_exc()}")
                sys.exit(1)
        
        print("[check_apt_packages] Done.\n")
        return True