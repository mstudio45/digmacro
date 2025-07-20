__all__ = ["check_package_version"]

def normalize_version(v): 
    return [int(part) if part.isdigit() else part for part in v.replace("-", ".").split(".")]

def check_package_version(installed, required, check_if_equal=True):
    if check_if_equal == True:
        return normalize_version(installed) >= normalize_version(required)
    return normalize_version(installed) > normalize_version(required)
