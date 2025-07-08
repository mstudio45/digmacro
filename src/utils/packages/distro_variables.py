import csv, os, sys, glob, subprocess, platform, traceback
import utils.general.filehandler as FileHandler

__all__ = [
    "install_pip_package", 
    "current_os", "distro_id", "distro_name", "distro_key"
]

current_os = platform.system()
machine = platform.machine()

# install pip handler #
def get_platform_tag():
    if current_os == "Linux":
        if machine == "x86_64":
            return "manylinux2014_x86_64"
        elif machine == "aarch64":
            return "manylinux2014_aarch64"
    elif current_os == "Windows":
        if machine in ("AMD64", "x86_64"):
            return "win_amd64"
        elif machine == "ARM64":
            return "win_arm64"
    elif current_os == "Darwin":
        if machine == "x86_64":
            return "macosx_10_9_x86_64"
        elif machine == "arm64":
            return "macosx_11_0_arm64"

    raise f"Unsupported platform: {current_os} {machine}"

platform_tag = get_platform_tag()
if "Unsupported" in platform_tag:
    print(platform_tag)
    sys.exit(1)

def install_pip_package(package):
    try: 
        if package["version"] != "all":
            pip_spec = f"{package["pip"]}>={package["version"]}"
        else:
            pip_spec = package["pip"]
            
        print(f"[install_pip_package] Installing package: {pip_spec}")
        folder_path = f".pip_temp/{package["pip"]}"
        if not FileHandler.create_folder(folder_path):
            raise RuntimeError(f"Failed to create temp folder for {pip_spec}")

        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--force-reinstall", "--no-cache-dir",

            "--only-binary=:all:",
            "--platform", platform_tag,
            "--implementation", "cp",
            "--python-version", f"{sys.version_info.major}{sys.version_info.minor}",
            "--abi", f"cp{sys.version_info.major}{sys.version_info.minor}",
            "--target", os.path.abspath(folder_path),

            pip_spec
        ])

        wheel_files = glob.glob(os.path.join(folder_path, "*.whl"))
    
        if not wheel_files:
            FileHandler.try_delete_folder(folder_path)
            raise RuntimeError(f"No wheel files found after downloading {pip_spec}")
        
        # Step 3: Install the downloaded wheel file(s)
        for wheel_file in wheel_files:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "--force-reinstall", "--no-cache-dir",
                wheel_file
            ])
        
        FileHandler.try_delete_folder(folder_path)
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
    is_fedora           = distro_id in [ "fedora" ]
    is_arch_based       = distro_id in [ "arch", "manjaro", "endeavouros", "garuda" ]
    is_opensuse_based   = distro_id in [ "opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed" ]

    if (is_ubuntu_based or is_fedora or is_arch_based or is_opensuse_based) == False:
        print(f"{distro_name} ({distro_id}) is not supported.")
        sys.exit(1)

    if is_ubuntu_based:         distro_key = "ubuntu_based"
    elif is_fedora:             distro_key = "fedora"
    elif is_arch_based:         distro_key = "arch_based"
    elif is_opensuse_based:     distro_key = "opensuse_based"

    # linux functions #
    def get_linux_app_install_cmd():
        if is_ubuntu_based:
            return ["sudo", "apt-get", "install", "-y"]
        
        elif is_fedora:
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

        elif is_fedora:
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

            elif is_fedora:
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
