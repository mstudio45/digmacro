import csv, sys, subprocess, platform, traceback

__all__ = [
    "install_pip_package", 
    "current_os", "distro_id", "distro_name", "distro_key"
]

current_os = platform.system()
current_arch = platform.machine()

def install_pip_package(package):
    try: 
        if package["version"] != "all":
            pip_spec = f"{package["pip"]}>={package["version"]}"
        else:
            pip_spec = package["pip"]

        print(f"[install_pip_package] Installing package: {pip_spec}")
        
        command = [sys.executable, "-m", "pip", "install", pip_spec]
        if current_os == "Darwin":
            if package == "opencv-python":
                macos_ver = platform.mac_ver()
                if macos_ver is not None and macos_ver[0].startswith("12"):
                    pip_spec = f"{package["pip"]}==4.10.0.84"
                    print("Using an older version of opencv-python for faster install.")
            
            print(f"Using arch -{current_arch} prefix.")
            command = ["arch", f"-{current_arch}", sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", pip_spec]

        subprocess.check_call(command)
    except Exception as e:
        print(f"[install_pip_package] Failed to install '{package["pip"]}' requirement: \n{traceback.format_exc()}")
        sys.exit(1)

if current_os != "Linux":
    distro_id, distro_name, distro_key = current_os, current_os, "all"
else:
    __all__ = __all__ + ["get_linux_app_install_cmd", "get_linux_installed_packages"]
    def get_distro(): # https://majornetwork.net/2019/11/get-linux-distribution-name-and-version-with-python/ #
        RELEASE_DATA = {}
        
        with open("/etc/os-release") as f:
            reader = csv.reader(f, delimiter="=")
            for row in reader:
                if row: RELEASE_DATA[row[0]] = row[1]

        return RELEASE_DATA["ID"].lower(), RELEASE_DATA["NAME"]

        
    # variables #
    distro_id, distro_name = get_distro()
    distro_key = ""

    is_ubuntu_based     = distro_id in [ "debian", "ubuntu", "raspbian", "linuxmint", "pop", "elementary", "zorin" ]
    is_rhel_based       = distro_id in [ "rhel", "fedora", "bazzite" ]
    is_arch_based       = distro_id in [ "arch", "manjaro", "endeavouros", "garuda" ]
    is_opensuse_based   = distro_id in [ "opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed" ]

    if is_ubuntu_based:         distro_key = "ubuntu_based"
    elif is_rhel_based:         distro_key = "rhel_based"
    elif is_arch_based:         distro_key = "arch_based"
    elif is_opensuse_based:     distro_key = "opensuse_based"

    print(f"[INFO] Detected Linux distro: {distro_name} ({distro_id}), using key '{distro_key}'")
    if (is_ubuntu_based or is_rhel_based or is_arch_based or is_opensuse_based) == False:
        print(f"{distro_name} ({distro_id} - {distro_key}) is not supported. If your Linux Distro supports PyGObject, PyWebView and GTK make an feature request in the Discord Server to request official support for your Linux Distro.")
        sys.exit(1)

    # linux functions #
    def get_linux_app_install_cmd():
        if is_ubuntu_based:
            return ["sudo", "apt-get", "install", "-y"]
        
        elif is_rhel_based:
            return ["sudo", "dnf", "install", "-y"]
        
        elif is_arch_based:
            return ["sudo", "pacman", "-S", "--noconfirm"]
        
        elif is_opensuse_based:
            return ["sudo", "zypper", "install", "-y"]
        
        else:
            return f"Package install command not recognized for distro: {distro_name} ({distro_id})"

    def get_linux_installed_packages():
        if is_ubuntu_based:
            cmd = ["dpkg-query", "-W", "-f=${Package}\n"]

        elif is_rhel_based:
            cmd = ["dnf", "list", "installed"]

        elif is_arch_based:
            cmd = ["pacman", "-Qq"]

        elif is_opensuse_based:
            cmd = ["zypper", "se", "-i"]
        
        else:
            return f"Unsupported distro for listing installed packages: {distro_name} ({distro_id})"
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            output = result.stdout.strip()
            packages = []

            if is_ubuntu_based:
                packages = output.split("\n")

            elif is_rhel_based:
                lines = output.split("\n")
                packages = [line.split()[0] for line in lines if line and not line.startswith("Installed Packages")]

            elif is_arch_based:
                packages = output.split("\n")

            elif is_opensuse_based:
                lines = output.split("\n")
                for line in lines:
                    parts = line.split("|")
                    if len(parts) > 1 and parts[0].strip() == "i":
                        packages.append(parts[1].strip())

            return packages

        except Exception as e:
            print(f"Failed to list installed packages: {e}")
            return []
