import os, shutil

def write(filename, content):
    try:
        with open(file=filename, mode="w") as f:
            f.write(content)
            f.close()
        return True
    except Exception as e:
        print(f"[FileHandler.write] Failed to save '{str(filename)}': {e}")
        return False
    
def read(filename):
    try:
        content = None
        with open(file=filename, mode="r") as f:
            content = str(f.read())
            f.close()
        
        return content
    except Exception as e:
        print(f"[FileHandler.write] Failed to save '{str(filename)}': {e}")
        return None

# folders #
def create_folder(folderpath):
    try:
        if not os.path.isdir(folderpath):
            os.makedirs(folderpath)
        
        return True
    except Exception as e:
        print(f"[FileHandler.create_folder] Failed to create folder '{str(folderpath)}': {e}")
        return False
    
def is_folder_empty(folderpath):
    try:
        if not os.path.isdir(folderpath):
            return len(os.listdir(folderpath)) > 0
        return False
    except Exception as e:
        print(f"[FileHandler.is_folder_empty] Failed to check folder '{str(folderpath)}': {e}")
        return False
    
def try_delete_folder(folderpath):
    try:
        if not os.path.isdir(folderpath):
            shutil.rmtree(folderpath)
            return True
        return False
    except Exception as e:
        print(f"[FileHandler.is_folder_empty] Failed to check folder '{str(folderpath)}': {e}")
        return False