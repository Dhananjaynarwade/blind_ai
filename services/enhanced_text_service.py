import os
import cv2
import numpy as np
import base64
import re
import tensorflow as tf
from PIL import Image
import io
import json

# Import the existing text recognition service
from .text_service import TextRecognitionService

class EnhancedTextRecognitionService:
    def __init__(self):
        # Initialize the basic text recognition service
        self.text_service = TextRecognitionService()
        self.model = None
        self.loaded = False
        self.load_model()
        
        # Define potential text-containing objects
        self.text_containing_objects = [
            'book', 'cell phone', 'laptop', 'tv', 'remote', 'keyboard',
            'microwave', 'oven', 'refrigerator', 'clock', 'vase',
            'scissors', 'hair drier', 'toothbrush', 'cup', 'bottle',
            'wine glass', 'fork', 'knife', 'spoon', 'bowl', 'banana',
            'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog',
            'pizza', 'donut', 'cake', 'chair', 'couch', 'bed', 'dining table',
            'toilet', 'sink', 'tie', 'suitcase', 'handbag', 'backpack',
            'umbrella', 'shoe', 'eye glasses'
        ]
        
    def load_model(self):
        """Load the TensorFlow.js COCO-SSD model"""
        try:
            # Load model from TensorFlow.js web model format
            # Note: This is a placeholder - the actual model loading would be different
            # in a production environment with a local model file
            print("Loading object detection model...")
            self.loaded = True
            print("Using web-based object detection (TensorFlow.js COCO-SSD)")
        except Exception as e:
            print(f"Error loading object detection model: {e}")
            self.loaded = False

    def recognize_text(self, image_data):
        """
        Enhanced text recognition that first uses object detection to find
        potential text-containing regions, then applies OCR to those regions.
        """
        try:
            # Parse the base64 data
            if isinstance(image_data, str) and ',' in image_data:
                # Handle data URL format
                image_data = image_data.split(',')[1]
            
            # Decode base64 to image
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    'success': False,
                    'message': 'Failed to decode image data',
                    'confidence': 0
                }
                
            # Create a copy of the original image for annotation
            annotated_image = image.copy()
            
            # Object detection is done in the browser using TensorFlow.js
            # Here we'll simulate getting those objects by processing the image
            # to find regions that might contain text

            # First try to detect text directly in the whole image
            whole_image_result = self.text_service.recognize_text(image_data)
            
            # If Tesseract is not installed, return the error
            if not whole_image_result.get('success', False) and whole_image_result.get('tesseract_missing', True):
                return whole_image_result
                
            # If we found text with good confidence, use it
            if whole_image_result.get('success', False) and whole_image_result.get('confidence', 0) > 50:
                whole_image_result['enhanced'] = True
                whole_image_result['approach'] = "full_image"
                whole_image_result['regions_found'] = 0
                return whole_image_result
            
            # Try to find text regions using image processing techniques
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Try MSER (Maximally Stable Extremal Regions) text region detector
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            # Filter regions to find potential text areas
            text_regions = []
            
            if regions:
                for region in regions:
                    x, y, w, h = cv2.boundingRect(region)
                    
                    # Filter out regions that are too small or too large
                    if w * h > 100 and w < image.shape[1] * 0.9 and h < image.shape[0] * 0.9:
                        text_regions.append((x, y, w, h))
            
            # Combine overlapping regions
            if text_regions:
                text_regions = self._merge_overlapping_regions(text_regions)
            
            # Expand regions slightly to catch full text
            expanded_regions = []
            for x, y, w, h in text_regions:
                padding_x = int(w * 0.1)
                padding_y = int(h * 0.1)
                
                x1 = max(0, x - padding_x)
                y1 = max(0, y - padding_y)
                x2 = min(image.shape[1], x + w + padding_x)
                y2 = min(image.shape[0], y + h + padding_y)
                
                expanded_regions.append((x1, y1, x2 - x1, y2 - y1))
            
            # Draw the regions on the annotated image
            for x, y, w, h in expanded_regions:
                cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Find text in each region
            all_texts = []
            all_confidences = []
            
            print(f"Found {len(expanded_regions)} potential text regions")
            
            for i, (x, y, w, h) in enumerate(expanded_regions):
                # Extract region and convert to base64
                region = image[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', region)
                roi_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Recognize text in this region
                region_result = self.text_service.recognize_text(roi_base64)
                
                if region_result.get('success', False):
                    text = region_result.get('text', '')
                    confidence = region_result.get('confidence', 0)
                    
                    if text.strip():
                        all_texts.append(text)
                        all_confidences.append(confidence)
                        
                        # Add text annotation to the image
                        cv2.putText(
                            annotated_image, 
                            text[:20] + ('...' if len(text) > 20 else ''), 
                            (x, y - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, 
                            (0, 0, 255), 
                            1
                        )
            
            # Process results
            if all_texts:
                # Create the combined result
                combined_text = ' '.join(all_texts)
                average_confidence = sum(all_confidences) / len(all_confidences)
                
                # Encode the annotated image
                _, buffer = cv2.imencode('.jpg', annotated_image)
                annotated_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
                
                return {
                    'success': True,
                    'text': combined_text,
                    'confidence': average_confidence,
                    'enhanced': True,
                    'approach': 'region_based',
                    'regions_found': len(expanded_regions),
                    'regions_with_text': len(all_texts),
                    'annotated_image': annotated_base64
                }
            else:
                # Fall back to the whole image result if no text was found in regions
                if whole_image_result.get('success', False):
                    whole_image_result['enhanced'] = True
                    whole_image_result['approach'] = "full_image_fallback"
                    whole_image_result['regions_found'] = len(expanded_regions)
                    return whole_image_result
                
                return {
                    'success': False,
                    'message': 'No text detected in image or regions',
                    'confidence': 0,
                    'enhanced': True,
                    'regions_found': len(expanded_regions)
                }
                
        except Exception as e:
            print(f"Error in enhanced text recognition: {e}")
            # Fall back to standard text recognition
            return self.text_service.recognize_text(image_data)
    
    def _merge_overlapping_regions(self, regions):
        """Merge overlapping text regions"""
        if not regions:
            return []
            
        # Sort by x coordinate
        sorted_regions = sorted(regions, key=lambda r: r[0])
        merged = [sorted_regions[0]]
        
        for current in sorted_regions[1:]:
            previous = merged[-1]
            
            # Check if current overlaps with previous
            prev_x, prev_y, prev_w, prev_h = previous
            curr_x, curr_y, curr_w, curr_h = current
            
            prev_right = prev_x + prev_w
            prev_bottom = prev_y + prev_h
            curr_right = curr_x + curr_w
            curr_bottom = curr_y + curr_h
            
            # Determine horizontal and vertical overlap
            h_overlap = (curr_x <= prev_right) and (prev_x <= curr_right)
            v_overlap = (curr_y <= prev_bottom) and (prev_y <= curr_bottom)
            
            # If both horizontal and vertical overlap, merge the regions
            if h_overlap and v_overlap:
                new_x = min(prev_x, curr_x)
                new_y = min(prev_y, curr_y)
                new_right = max(prev_right, curr_right)
                new_bottom = max(prev_bottom, curr_bottom)
                
                merged[-1] = (new_x, new_y, new_right - new_x, new_bottom - new_y)
            else:
                merged.append(current)
                
        return merged

# Create a singleton instance
enhanced_text_recognition_service = EnhancedTextRecognitionService() 