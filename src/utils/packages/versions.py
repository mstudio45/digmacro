__all__ = ["is_version_outdated", "is_version_over_required"]

def normalize_version(v): 
    return [int(part) if part.isdigit() else part for part in v.replace("-", ".").split(".")]

def is_version_outdated(current, latest):
    return normalize_version(current) < normalize_version(latest)

def is_version_over_required(current, required):
    return normalize_version(current) > normalize_version(required)