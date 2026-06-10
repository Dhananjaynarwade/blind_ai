import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

class TextAnnotationService:
    def __init__(self):
        """Initialize the text annotation service"""
        self.last_annotated_image = None
        self.font_path = self._find_font()
    
    def _find_font(self):
        """Find a usable font for text annotations"""
        # Check common font locations based on OS
        import platform
        system = platform.system()
        
        if system == 'Windows':
            font_paths = [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'verdana.ttf'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'calibri.ttf')
            ]
        elif system == 'Darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/Helvetica.ttc',
                '/System/Library/Fonts/Arial.ttf',
                '/Library/Fonts/Arial.ttf'
            ]
        else:  # Linux and others
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/TTF/Arial.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
            ]
        
        # Try to find a usable font
        for path in font_paths:
            if os.path.exists(path):
                return path
        
        # No font found, will use default OpenCV font
        return None
    
    def highlight_text_regions(self, image_data, regions):
        """Highlight detected text regions in the image
        
        Args:
            image_data: Base64 encoded image
            regions: List of [x, y, w, h] regions where text was detected
            
        Returns:
            Base64 encoded image with highlighted regions
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image data")
            
            # Create a copy of the image
            annotated_image = image.copy()
            
            # Draw rectangles around text regions
            for region in regions:
                x, y, w, h = region
                cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Convert back to base64
            _, buffer = cv2.imencode('.jpg', annotated_image)
            annotated_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
            
            # Store the annotated image
            self.last_annotated_image = annotated_base64
            
            return {
                'success': True,
                'annotated_image': annotated_base64
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error highlighting text: {str(e)}"
            }
    
    def add_text_overlay(self, image_data, text, position=None, color=(0, 255, 0), size=30):
        """Add text overlay to an image
        
        Args:
            image_data: Base64 encoded image
            text: Text to overlay
            position: (x, y) position tuple, or None for auto-positioning
            color: (r, g, b) color tuple
            size: Font size
            
        Returns:
            Base64 encoded image with text overlay
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            
            # Use PIL for better font rendering
            pil_image = Image.open(BytesIO(image_bytes))
            
            # Create a drawing context
            draw = ImageDraw.Draw(pil_image)
            
            # Auto-position if no position specified
            if position is None:
                position = (20, 20)  # Default top-left with padding
            
            # Use a proper font if available, otherwise use default
            if self.font_path:
                try:
                    font = ImageFont.truetype(self.font_path, size)
                    draw.text(position, text, fill=color, font=font)
                except Exception as e:
                    print(f"Error using TrueType font: {e}")
                    # Fallback to default font
                    draw.text(position, text, fill=color)
            else:
                # Use default font
                draw.text(position, text, fill=color)
            
            # Convert back to base64
            buffer = BytesIO()
            pil_image.save(buffer, format="JPEG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            annotated_base64 = 'data:image/jpeg;base64,' + img_str
            
            # Store the annotated image
            self.last_annotated_image = annotated_base64
            
            return {
                'success': True,
                'annotated_image': annotated_base64
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error adding text overlay: {str(e)}"
            }
    
    def create_annotated_image_with_detections(self, image_data, detected_text, confidence_threshold=40):
        """Create an image with the detected text highlighted and annotated
        
        Args:
            image_data: Base64 encoded image
            detected_text: The text that was detected in the image
            confidence_threshold: Minimum confidence score for annotations
            
        Returns:
            Base64 encoded image with text annotations
        """
        try:
            # Decode base64 image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image data")
            
            # Create a copy of the image
            annotated_image = image.copy()
            height, width = annotated_image.shape[:2]
            
            # Add a semi-transparent overlay to make text more readable
            overlay = annotated_image.copy()
            cv2.rectangle(overlay, (0, height - 100), (width, height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, annotated_image, 0.5, 0, annotated_image)
            
            # Add detected text at the bottom
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_to_display = detected_text[:100] + "..." if len(detected_text) > 100 else detected_text
            cv2.putText(annotated_image, "Detected Text:", (20, height - 70), font, 0.7, (255, 255, 255), 2)
            
            # Split text into multiple lines if needed
            max_width = width - 40  # Margin on both sides
            words = text_to_display.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                # Estimate text width
                (text_width, _), _ = cv2.getTextSize(test_line, font, 0.6, 1)
                
                if text_width <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
                    
            if current_line:
                lines.append(current_line)
            
            # Draw lines of text
            for i, line in enumerate(lines[:2]):  # Limit to 2 lines
                y_position = height - 45 + (i * 25)
                cv2.putText(annotated_image, line, (20, y_position), font, 0.6, (255, 255, 255), 1)
            
            # Convert back to base64
            _, buffer = cv2.imencode('.jpg', annotated_image)
            annotated_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
            
            # Store the annotated image
            self.last_annotated_image = annotated_base64
            
            return {
                'success': True,
                'annotated_image': annotated_base64
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error creating annotated image: {str(e)}"
            }
    
    def get_last_annotated_image(self):
        """Return the last annotated image"""
        return self.last_annotated_image

# Create singleton instance
text_annotation_service = TextAnnotationService() 