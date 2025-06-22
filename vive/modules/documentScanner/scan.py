import cv2
import numpy as np
from PIL import Image, ImageEnhance
import os
import io
import time
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from .fileHandler import DocumentFileHandler

class DocumentScanner:
    def __init__(self, inbox_dir="inbox", output_dir="inbox"):
        self.file_handler = DocumentFileHandler(inbox_dir, output_dir)
    
    def load_image(self, image_path):
        """Load image from file path"""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        return image
    
    def find_document_contour(self, image):
        """Find the largest rectangular contour (document edges)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 75, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        # Find the contour with 4 vertices (rectangular)
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:
                return approx
        
        # If no perfect rectangle found, use the largest contour
        if contours:
            return contours[0]
        return None
    
    def order_points(self, pts):
        """Order points in top-left, top-right, bottom-right, bottom-left order"""
        rect = np.zeros((4, 2), dtype="float32")
        
        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        rect[0] = pts[np.argmin(s)]      # top-left
        rect[2] = pts[np.argmax(s)]      # bottom-right
        rect[1] = pts[np.argmin(diff)]   # top-right
        rect[3] = pts[np.argmax(diff)]   # bottom-left
        
        return rect
    
    def perspective_transform(self, image, pts):
        """Apply perspective transformation to get top-down view"""
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect
        
        # Calculate width and height of the new image
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Define destination points
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Apply perspective transformation
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def enhance_document(self, image):
        """Enhance the document image (brightness, contrast, sharpness)"""
        # Convert to PIL for enhancement
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1.05)
        
        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def resize_to_a4(self, image):
        """Resize image to A4 proportions"""
        h, w = image.shape[:2]
        a4_ratio = 297.0 / 210.0  # A4 height/width ratio
        
        if h / w > a4_ratio:
            # Image is taller than A4 ratio
            new_h = int(w * a4_ratio)
            new_w = w
        else:
            # Image is wider than A4 ratio
            new_w = int(h / a4_ratio)
            new_h = h
        
        # Resize image
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized
    
    def save_as_pdf(self, image, output_path):
        """Save the processed image as PDF"""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # Create PDF
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Calculate dimensions to fit A4
        img_width, img_height = pil_image.size
        page_width, page_height = A4
        
        # Scale to fit page while maintaining aspect ratio
        scale = min(page_width / img_width, page_height / img_height)
        scaled_width = img_width * scale
        scaled_height = img_height * scale
        
        # Center the image
        x = (page_width - scaled_width) / 2
        y = (page_height - scaled_height) / 2
        
        # Save image to temporary buffer
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Draw image on PDF
        c.drawImage(ImageReader(img_buffer), x, y, scaled_width, scaled_height)
        c.save()
        
        return output_path
    
    def process_document(self, image_path, auto_detect=True, enhance=True, save_pdf=True):
        """
        Main function to process a document image
        """
        try:
            # Load image
            original = self.load_image(image_path)
            processed = original.copy()
            
            # Auto-detect and correct perspective if enabled
            if auto_detect:
                contour = self.find_document_contour(original)
                if contour is not None and len(contour) >= 4:
                    # If we found a good contour, apply perspective correction
                    if len(contour) == 4:
                        processed = self.perspective_transform(processed, contour.reshape(4, 2))
                    else:
                        # Use bounding rectangle of the contour
                        rect = cv2.boundingRect(contour)
                        x, y, w, h = rect
                        processed = processed[y:y+h, x:x+w]
            
            # Enhance image quality
            if enhance:
                processed = self.enhance_document(processed)
            
            # Resize to A4 proportions
            processed = self.resize_to_a4(processed)
            
            # Generate output paths using file handler
            processed_img_path, pdf_path = self.file_handler.generate_output_paths(image_path)
            
            # Save processed image
            cv2.imwrite(processed_img_path, processed)
            
            # Save as PDF if requested
            if save_pdf:
                self.save_as_pdf(processed, pdf_path)
            else:
                pdf_path = None
            
            return {
                "success": True,
                "original_path": image_path,
                "processed_image": processed_img_path,
                "pdf_path": pdf_path,
                "message": "Document processed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process document"
            }

# Convenience functions
def process_inbox(inbox_dir="inbox", output_dir="inbox", move_originals=False, delete_originals=False):
    """Process all documents in inbox folder"""
    scanner = DocumentScanner(inbox_dir, output_dir)
    return scanner.file_handler.auto_process_inbox(scanner, move_originals, delete_originals)

def watch_inbox(inbox_dir="inbox", output_dir="inbox", interval=5):
    """Watch inbox folder for new documents"""
    scanner = DocumentScanner(inbox_dir, output_dir)
    scanner.file_handler.watch_inbox(scanner, interval)

def get_stats(inbox_dir="inbox", output_dir="inbox"):
    """Get file statistics"""
    file_handler = DocumentFileHandler(inbox_dir, output_dir)
    return file_handler.get_file_stats()

# if __name__ == "__main__":
#     # Example usage
#     result = process_inbox(move_originals=True)
#     print("\nProcessing Summary:")
#     print(f"Total files: {result['total_files']}")
#     print(f"Processed: {result['processed']}")
#     print(f"Failed: {result['failed']}")
#     print(f"Message: {result['message']}")
    
#     # Show statistics
#     stats = get_stats()
#     print(f"\nFile Statistics:")
#     print(f"Inbox files: {stats['inbox_files']}")
#     print(f"Output files: {stats['output_files']}")
#     print(f"Processed files: {stats['processed_files']}")