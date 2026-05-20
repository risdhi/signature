# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SignaturePreprocessor:
    """Preprocess signature images for model input"""
    
    def __init__(self, target_size=(105, 105)):
        """
        Initialize preprocessor
        
        Args:
            target_size: Target image size (height, width)
        """
        self.target_size = target_size
    
    def load_image(self, image_path, color_mode='grayscale'):
        """
        Load image from file
        
        Args:
            image_path: Path to image file
            color_mode: 'color' or 'grayscale'
            
        Returns:
            Loaded image
        """
        # Always load as grayscale
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
        return img
    
    def to_grayscale(self, image):
        """Convert to grayscale"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return image
    
    def apply_adaptive_threshold(self, gray_image, block_size=11, C=2):
        """
        Apply adaptive thresholding
        
        Args:
            gray_image: Grayscale image
            block_size: Size of pixel neighborhood (must be odd)
            C: Constant subtracted
            
        Returns:
            Binary image
        """
        if block_size % 2 == 0:
            block_size += 1
        
        binary = cv2.adaptiveThreshold(
            gray_image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size, C
        )
        return binary
    
    def denoise(self, image, h=10, template_size=7, search_size=21):
        """
        Denoise image using bilateral filter
        
        Args:
            image: Input image
            h: Filter strength
            template_size: Size of template patch
            search_size: Size of search area
            
        Returns:
            Denoised image
        """
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Use positional arguments for OpenCV 4.8.1 compatibility
            denoised = cv2.fastNlMeansDenoisingColored(
                image,
                None,
                h,
                h,
                template_size,
                search_size
            )
        else:
            denoised = cv2.fastNlMeansDenoising(
                image,
                None,
                h,
                template_size,
                search_size
            )
        return denoised
    
    def remove_background(self, image):
        """
        Remove background using morphological operations
        
        Args:
            image: Binary image
            
        Returns:
            Cleaned image
        """
        # Create kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # Morphological closing (fill small holes)
        closed = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        
        # Morphological opening (remove small noise)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
        
        return opened
    
    def extract_contours(self, binary_image):
        """
        Extract signature contours
        
        Args:
            binary_image: Binary image
            
        Returns:
            Contour image, contours
        """
        contours, _ = cv2.findContours(
            binary_image,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Create contour image
        contour_img = np.zeros_like(binary_image)
        cv2.drawContours(contour_img, contours, -1, 255, 2)
        
        return contour_img, contours
    
    def auto_crop(self, image):
        """
        Auto-crop image to signature region
        
        Args:
            image: Binary image
            
        Returns:
            Cropped image
        """
        # Find non-zero coordinates
        coords = cv2.findNonZero(image)
        
        if coords is None:
            return image
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(coords)
        
        # Add padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)
        
        # Crop
        cropped = image[y:y+h, x:x+w]
        
        return cropped
    
    def resize_with_padding(self, image, size=None, fill_color=255):
        """
        Resize image with padding to maintain aspect ratio
        
        Args:
            image: Input image
            size: Target size (height, width)
            fill_color: Padding color
            
        Returns:
            Resized image with padding
        """
        if size is None:
            size = self.target_size
        
        h, w = image.shape[:2]
        target_h, target_w = size
        
        # Calculate aspect ratio
        aspect = w / h
        target_aspect = target_w / target_h
        
        if aspect > target_aspect:
            # Image is wider
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            # Image is taller
            new_h = target_h
            new_w = int(target_h * aspect)
        
        # Resize
        resized = cv2.resize(image, (new_w, new_h))
        
        # Create canvas
        canvas = np.full((target_h, target_w), fill_color, dtype=image.dtype)
        
        # Calculate offset
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        
        # Place resized image on canvas
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
    
    def process(self, image_path, output_path=None):
        """
        Full preprocessing pipeline
        
        Args:
            image_path: Path to input image
            output_path: Optional path to save processed image
            
        Returns:
            Processed image as numpy array
        """
        try:
            logger.info(f"Processing image: {image_path}")
            
            # Load image
            image = self.load_image(image_path, color_mode='color')
            logger.debug(f"Loaded image shape: {image.shape}")
            
            # Denoise
            image = self.denoise(image)
            logger.debug("Applied denoising")
            
            # Convert to grayscale
            gray = self.to_grayscale(image)
            
            # Apply adaptive threshold
            binary = self.apply_adaptive_threshold(gray)
            logger.debug("Applied adaptive threshold")
            
            # Remove background
            cleaned = self.remove_background(binary)
            logger.debug("Removed background")
            
            # Auto crop
            cropped = self.auto_crop(cleaned)
            logger.debug(f"Auto-cropped to: {cropped.shape}")
            
            # Resize with padding
            processed = self.resize_with_padding(cropped, self.target_size)
            logger.debug(f"Resized to: {processed.shape}")
            
            # Convert back to 3-channel for model input
            if len(processed.shape) == 2:
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            
            # Save if output path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(output_path), cv2.cvtColor(processed, cv2.COLOR_RGB2BGR))
                logger.info(f"Saved processed image: {output_path}")
            
            logger.info(f"Processing completed successfully: {processed.shape}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise


# Singleton instance
_preprocessor = None


def get_preprocessor(target_size=(105, 105)):
    """Get or create preprocessor instance"""
    global _preprocessor
    
    if _preprocessor is None or _preprocessor.target_size != target_size:
        _preprocessor = SignaturePreprocessor(target_size)
    
    return _preprocessor


def preprocess_signature(image_path, output_path=None, target_size=(105, 105)):
    """Preprocess signature image"""
    preprocessor = get_preprocessor(target_size)
    return preprocessor.process(image_path, output_path)
