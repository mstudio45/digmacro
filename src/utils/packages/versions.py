__all__ = ["check_package_version"]

def normalize_version(v): 
    return [int(part) if part.isdigit() else part for part in v.replace("-", ".").split(".")]

def check_package_version(installed, required): # check if installed version is over or equal the required version #
    return normalize_version(installed) >= normalize_version(required)
