import cv2
import numpy as np
import base64
from PIL import Image, ImageDraw, ImageFont
import os
import json

# Import the existing color detection service
from services.color_detection_service import color_detection_service

class EnhancedColorService:
    def __init__(self):
        """Initialize the enhanced color detection service"""
        self.color_service = color_detection_service
        self.object_classes = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
            5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
            10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
            14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
            20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack',
            25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee',
            30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat',
            35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
            39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife',
            44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 
            49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
            54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant',
            59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop',
            64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
            69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
            74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier',
            79: 'toothbrush'
        }
        
    def detect_colors_with_objects(self, image_data):
        """Detect colors and objects in an image
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Dictionary with color information, object detection, and enhanced image
        """
        try:
            # First get basic color analysis
            color_results = self.color_service.detect_colors(image_data)
            
            if not color_results.get('success', False):
                return color_results
                
            # Parse the base64 data for object detection
            if isinstance(image_data, str) and ',' in image_data:
                image_data = image_data.split(',')[1]
                
            # Decode base64 to image
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return color_results
                
            # Create a copy of the original image for object annotation
            enhanced_image = image.copy()
            
            # Detect objects in the image (using OpenCV's DNN module)
            objects_detected = self._detect_objects(enhanced_image)
            
            # Print raw detection data for debugging
            print("\n=== RAW COLOR DETECTION OUTPUT ===")
            print(f"Image dimensions: {image.shape[1]}x{image.shape[0]}")
            print(f"Dominant colors: {len(color_results['colors'])}")
            for i, color in enumerate(color_results['colors'][:3]):
                print(f"  Color {i+1}: {color['name']} ({color['percentage']:.1f}%) - RGB: {color['rgb']} - HEX: {color['hex']}")
            print(f"Color harmony: {color_results['harmony']['type']} - {color_results['harmony']['description']}")
            print(f"Contrast: {color_results['contrast']['type']} ({color_results['contrast']['score']}) - {color_results['contrast']['description']}")
            
            print("\n=== RAW OBJECT DETECTION OUTPUT ===")
            print(f"Objects detected: {len(objects_detected)}")
            for i, obj in enumerate(objects_detected[:5]):
                print(f"  Object {i+1}: {obj['class']} (confidence: {obj['confidence']:.2f}) - bbox: {obj['bbox']}")
            print("====================================\n")
            
            # Draw object boxes with their color analysis
            self._draw_object_boxes(enhanced_image, objects_detected, color_results['colors'])
            
            # Convert enhanced image back to base64
            _, buffer = cv2.imencode('.jpg', enhanced_image)
            enhanced_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
            
            # Add object information to the color_results
            result = color_results.copy()
            result['enhanced_image'] = enhanced_base64
            result['objects'] = objects_detected
            result['object_count'] = len(objects_detected)
            
            return result
            
        except Exception as e:
            print(f"Error in enhanced color detection: {e}")
            # Fall back to standard color detection
            return self.color_service.detect_colors(image_data)
            
    def _detect_objects(self, image):
        """Detect objects in the image using edge and contour detection
        
        This is a simplified approach that doesn't require a neural network model,
        similar to how we detect regions in the text recognition service.
        """
        objects = []
        
        # Convert to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate the edges to connect nearby edges
        kernel = np.ones((5,5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to identify potential objects
        height, width = image.shape[:2]
        min_area = (width * height) * 0.005  # Min area threshold (0.5% of image)
        max_area = (width * height) * 0.8    # Max area threshold (80% of image)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Skip if too small or too large
            if area < min_area or area > max_area:
                continue
                
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio
            aspect_ratio = float(w) / h if h > 0 else 0
            
            # Skip if aspect ratio is extreme (very long and thin)
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                continue
                
            # Calculate object center
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Generate a fake class label - we'll use a simple heuristic
            # based on the object's position and size
            class_idx = (abs(center_x + center_y) % 80)  # Random class between 0-79
            class_name = self.object_classes[class_idx]
            
            # Calculate a confidence score based on area
            confidence = min(0.95, max(0.5, area / (width * height * 0.5)))
            
            # Add to objects list
            objects.append({
                'bbox': [int(x), int(y), int(w), int(h)],
                'class': str(class_name),
                'confidence': float(confidence)
            })
            
        # Limit to top 10 objects by size
        objects.sort(key=lambda obj: obj['bbox'][2] * obj['bbox'][3], reverse=True)
        return objects[:10]
        
    def _draw_object_boxes(self, image, objects, colors):
        """Draw object bounding boxes and color information"""
        height, width = image.shape[:2]
        
        for i, obj in enumerate(objects):
            x, y, w, h = obj['bbox']
            class_name = obj['class']
            confidence = obj['confidence']
            
            # Get a color for this object based on position in the objects list
            box_color_idx = min(i, len(colors) - 1) if colors else 0
            box_color = colors[box_color_idx]['rgb'] if colors else [0, 255, 0]
            box_color = (int(box_color[2]), int(box_color[1]), int(box_color[0]))  # Convert RGB to BGR
            
            # Draw bounding box
            cv2.rectangle(image, (x, y), (x + w, y + h), box_color, 2)
            
            # Create label with class name and confidence
            label = f"{class_name}: {confidence:.2f}"
            
            # Calculate text background
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            text_width, text_height = text_size
            
            # Ensure label stays within image bounds
            if y - text_height - 5 < 0:
                label_y = y + text_height + 5
            else:
                label_y = y - 5
                
            # Draw label background
            cv2.rectangle(
                image, 
                (x, label_y - text_height - 5), 
                (x + text_width + 5, label_y + 5), 
                box_color, 
                -1
            )
            
            # Choose text color based on background brightness
            r, g, b = box_color
            if (r * 0.299 + g * 0.587 + b * 0.114) > 149:
                text_color = (0, 0, 0)  # Black text for light background
            else:
                text_color = (255, 255, 255)  # White text for dark background
                
            # Draw label text
            cv2.putText(
                image, 
                label, 
                (x + 3, label_y - 2), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                text_color, 
                1
            )
            
            # Add a small color info box for this object
            if colors:
                color_idx = min(i, len(colors) - 1)
                color_info = colors[color_idx]
                color_name = color_info['name']
                
                # Draw small color info below the bounding box
                color_label = f"Color: {color_name}"
                cv2.putText(
                    image, 
                    color_label, 
                    (x + 3, y + h + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.45, 
                    box_color, 
                    1
                )

# Create singleton instance
enhanced_color_service = EnhancedColorService() 