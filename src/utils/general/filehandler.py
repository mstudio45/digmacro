import os, shutil
import logging

def write(filename: str, content: str) -> bool:
    try:
        with open(file=filename, mode="w", encoding="utf-8") as f:
            f.write(content)

        logging.info(f"Successfully wrote content to '{filename}'.")
        return True
    
    except IOError as e:
        logging.error(f"Failed to write to '{filename}': {e}")
        return False
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while writing to '{filename}': {e}")
        return False

def read(filename: str) -> str | None:
    try:
        with open(file=filename, mode="r", encoding="utf-8") as f:
            content = f.read()
        
        logging.info(f"Successfully read content from '{filename}'.")
        return content
    
    except FileNotFoundError:
        logging.warning(f"File not found: '{filename}'.")
        return None
    
    except IOError as e:
        logging.error(f"Failed to read from '{filename}': {e}")
        return None
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading from '{filename}': {e}")
        return None

# folders #
def create_folder(folderpath: str) -> bool:
    try:
        os.makedirs(folderpath, exist_ok=True)

        logging.info(f"Folder '{folderpath}' created or already exists.")
        return True
    
    except OSError as e:
        logging.error(f"Failed to create folder '{folderpath}': {str(e)}")
        return False
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while creating folder '{folderpath}': {str(e)}")
        return False

def is_folder_empty(folderpath: str) -> bool:
    try:
        if not os.path.isdir(folderpath):
            logging.warning(f"Folder '{folderpath}' does not exist.")
            return False
        
        return len(os.listdir(folderpath)) == 0
    
    except OSError as e:
        logging.error(f"Failed to access folder '{folderpath}': {e}")
        return False
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while checking folder '{folderpath}': {e}")
        return False

def try_delete_folder(folderpath: str) -> bool:
    try:
        if os.path.isdir(folderpath):
            shutil.rmtree(folderpath)
            logging.info(f"Successfully deleted folder '{folderpath}'.")
            return True
        else:
            logging.info(f"Folder '{folderpath}' does not exist, no deletion needed.")
            return True
        
    except OSError as e:
        logging.error(f"Failed to delete folder '{folderpath}': {e}")
        return False
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while deleting folder '{folderpath}': {e}")
        return False