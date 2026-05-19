import os
import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder):
    """
    Save uploaded file and return path
    
    Args:
        file: Flask FileStorage object
        upload_folder: Folder to save to
        
    Returns:
        Path to saved file
    """
    if not file or file.filename == '':
        raise ValueError("No file selected")
    
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Create folder if doesn't exist
    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = int(np.random.rand() * 1e9)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"sig_{timestamp}.{ext}"
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    logger.info(f"File saved: {filepath}")
    return filepath


def get_image_dimensions(image_path):
    """Get image dimensions"""
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    return img.shape[:2]


def remove_file(filepath):
    """Safely remove file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"File removed: {filepath}")
    except Exception as e:
        logger.error(f"Error removing file {filepath}: {str(e)}")


def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error getting file size: {str(e)}")
        return 0


def list_files(folder, extension=None):
    """List files in folder"""
    files = []
    try:
        for filename in os.listdir(folder):
            if extension is None or filename.endswith(extension):
                files.append(os.path.join(folder, filename))
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
    
    return files
