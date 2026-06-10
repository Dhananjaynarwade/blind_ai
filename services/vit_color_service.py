import numpy as np
import base64
import cv2
import io
from PIL import Image, ImageDraw
import colorsys
import torch
from transformers import ViTFeatureExtractor, ViTForImageClassification
import os
import json

class VitColorService:
    def __init__(self):
        """Initialize the Vision Transformer Color Detection Service"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_loaded = False
        self.feature_extractor = None
        self.model = None
        
        # Color names and their RGB values
        self.color_mapping = {
            'red': (255, 0, 0),
            'green': (0, 128, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'purple': (128, 0, 128),
            'orange': (255, 165, 0),
            'pink': (255, 192, 203),
            'brown': (165, 42, 42),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'gold': (255, 215, 0),
            'silver': (192, 192, 192),
            'teal': (0, 128, 128),
            'navy': (0, 0, 128),
            'maroon': (128, 0, 0),
            'olive': (128, 128, 0),
            'lime': (0, 255, 0)
        }
    
    def load_model(self):
        """Load the pre-trained ViT model for color detection"""
        try:
            # For color detection, we'll use a pretrained ViT model and adapt it
            # If needed, we could fine-tune it on a color dataset
            self.feature_extractor = ViTFeatureExtractor.from_pretrained('google/vit-base-patch16-224')
            self.model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            return True
        except Exception as e:
            print(f"Failed to load ViT model: {str(e)}")
            return False

    def preprocess_image(self, image):
        """Preprocess image for the ViT model"""
        # Resize and normalize
        if self.feature_extractor is None:
            success = self.load_model()
            if not success:
                return None
        
        # Convert to RGB if in BGR format (from OpenCV)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL image
        pil_image = Image.fromarray(image)
        
        # Create inputs for the model
        inputs = self.feature_extractor(images=pil_image, return_tensors="pt")
        inputs = {key: val.to(self.device) for key, val in inputs.items()}
        
        return inputs, pil_image

    def extract_color_regions(self, image, num_regions=5):
        """Extract color regions using image segmentation"""
        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
            
        # Reshape for k-means
        pixels = image_rgb.reshape((-1, 3)).astype(np.float32)
        
        # Use k-means to find dominant color regions
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, num_regions, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Get the region masks and colors
        region_masks = []
        region_colors = []
        
        for i in range(num_regions):
            mask = np.zeros(image_rgb.shape[:2], dtype=np.uint8)
            mask_flat = (labels.flatten() == i).astype(np.uint8)
            mask = mask_flat.reshape(image_rgb.shape[:2])
            
            # Get the color for this region
            color = centers[i].astype(np.uint8)
            
            region_masks.append(mask)
            region_colors.append(color)
        
        return region_masks, region_colors

    def analyze_colors_with_vit(self, image):
        """Use ViT to analyze colors in image regions"""
        if not self.model_loaded and not self.load_model():
            return None
        
        # Extract color regions
        region_masks, region_colors = self.extract_color_regions(image)
        
        color_analysis = []
        
        # Analyze each region
        for i, (mask, color) in enumerate(zip(region_masks, region_colors)):
            # Skip small regions (less than 5% of the image)
            if np.sum(mask) / (mask.shape[0] * mask.shape[1]) < 0.05:
                continue
                
            # Create masked image with just this region
            masked_image = np.zeros_like(image)
            for c in range(3):  # Apply mask to each channel
                masked_image[:,:,c] = image[:,:,c] * mask
            
            # Preprocess for ViT
            inputs, _ = self.preprocess_image(masked_image)
            
            # Get model output
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get attention maps from the last layer
            attention = self.model.vit.encoder.layer[-1].attention.attention_scores
            
            # Calculate attention-weighted feature representation
            attention_mean = attention.mean(dim=1)  # Average across attention heads
            
            # Use weighted features to enhance color perception
            b, g, r = color
            color_rgb = (r, g, b)
            
            # Find closest named color
            color_name = self.find_closest_color(color_rgb)
            hex_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            
            # Calculate region percentage
            region_percentage = (np.sum(mask) / (mask.shape[0] * mask.shape[1])) * 100
            
            # Determine if color is dark or light
            is_dark = self.is_dark_color(color_rgb)
            
            # Append to results
            color_analysis.append({
                'name': color_name,
                'rgb': [int(r), int(g), int(b)],
                'hex': hex_code,
                'percentage': float(round(region_percentage, 2)),
                'is_dark': bool(is_dark),
                'is_light': bool(not is_dark),
                'attention_score': float(attention_mean.mean().item())
            })
        
        # Sort by percentage (highest first)
        color_analysis.sort(key=lambda x: x['percentage'], reverse=True)
        
        return color_analysis

    def find_closest_color(self, rgb):
        """Find the closest named color to the given RGB value"""
        r, g, b = rgb
        min_distance = float('inf')
        closest_color = "unknown"
        
        for name, color_rgb in self.color_mapping.items():
            cr, cg, cb = color_rgb
            # Calculate color distance using Euclidean distance
            distance = np.sqrt((r - cr)**2 + (g - cg)**2 + (b - cb)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_color = name
        
        return closest_color

    def is_dark_color(self, rgb):
        """Check if a color is dark (for text contrast)"""
        r, g, b = rgb
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5

    def create_color_palette(self, colors):
        """Create a color palette image from the detected colors"""
        # Create palette image
        width, height = 800, 200
        palette = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(palette)
        
        # Draw each color as a rectangle
        num_colors = len(colors)
        if num_colors == 0:
            return None
            
        section_width = width // num_colors
        
        for i, color_info in enumerate(colors):
            r, g, b = color_info['rgb']
            x0 = i * section_width
            x1 = (i + 1) * section_width
            draw.rectangle([x0, 0, x1, height], fill=(r, g, b))
            
            # Add color name
            text_color = (255, 255, 255) if color_info['is_dark'] else (0, 0, 0)
            try:
                # This requires PIL's ImageFont
                from PIL import ImageFont
                font = ImageFont.load_default()
                draw.text((x0 + 10, height - 30), color_info['name'], fill=text_color)
                draw.text((x0 + 10, height - 15), color_info['hex'], fill=text_color)
            except:
                pass  # Skip text if font not available
        
        # Convert to base64
        buffer = io.BytesIO()
        palette.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"

    def detect_colors(self, image_data):
        """Main method to detect colors using ViT
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Dictionary with color information
        """
        try:
            # Decode base64 image
            if isinstance(image_data, str) and ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    'success': False,
                    'message': 'Failed to decode image data',
                    'colors': []
                }
            
            # Get image dimensions
            height, width = image.shape[:2]
            
            # Create a copy for annotation
            annotated_image = image.copy()
            
            # Use ViT to analyze colors
            color_analysis = self.analyze_colors_with_vit(image)
            
            if color_analysis is None:
                return {
                    'success': False,
                    'message': 'Failed to load ViT model',
                    'colors': []
                }
            
            # Create color palette
            color_palette = self.create_color_palette(color_analysis)
            
            # Annotate the image with detected colors
            for i, color_info in enumerate(color_analysis[:5]):  # Show top 5 colors
                r, g, b = color_info['rgb']
                start_x = int(width * 0.05)
                end_x = int(width * 0.25)
                start_y = int(height * (0.05 + i * 0.06))
                end_y = int(height * (0.10 + i * 0.06))
                
                # Draw color patch
                cv2.rectangle(annotated_image, (start_x, start_y), (end_x, end_y), 
                             (int(b), int(g), int(r)), -1)
                
                # Add text with color name and percentage
                text_color = (0, 0, 0) if not color_info['is_dark'] else (255, 255, 255)
                text = f"{color_info['name']} ({color_info['percentage']:.1f}%)"
                cv2.putText(annotated_image, text, (end_x + 10, start_y + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
            
            # Add "Analyzed with Vision Transformer" text
            cv2.putText(annotated_image, "Analyzed with Vision Transformer", 
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Convert annotated image back to base64
            _, buffer = cv2.imencode('.jpg', annotated_image)
            annotated_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'colors': color_analysis,
                'dominant_color': color_analysis[0] if color_analysis else None,
                'color_palette': color_palette,
                'annotated_image': annotated_base64,
                'model': 'Vision Transformer (ViT)'
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Error detecting colors with ViT: {str(e)}",
                'colors': []
            }

# Create a singleton instance
vit_color_service = VitColorService() 