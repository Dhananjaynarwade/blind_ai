import cv2
import numpy as np
import base64
from PIL import Image, ImageDraw, ImageFont
import colorsys
import io
import json

class ColorDetectionService:
    def __init__(self):
        """Initialize the color detection service"""
        self.last_detected_colors = []
        self.color_names = {
            "red": ((0, 0, 180), (50, 50, 255)),
            "orange": ((0, 100, 200), (80, 165, 255)),
            "yellow": ((0, 180, 180), (50, 255, 255)),
            "green": ((40, 100, 0), (80, 255, 50)),
            "blue": ((170, 0, 0), (255, 50, 50)),
            "purple": ((170, 0, 170), (255, 50, 255)),
            "pink": ((150, 50, 200), (255, 140, 255)),
            "brown": ((0, 40, 80), (80, 100, 140)),
            "white": ((200, 200, 200), (255, 255, 255)),
            "black": ((0, 0, 0), (50, 50, 50)),
            "gray": ((70, 70, 70), (180, 180, 180))
        }

    def detect_colors(self, image_data):
        """Detect dominant colors in an image
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Dictionary with color information and enhanced image
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
            
            # Get dimensions for information
            height, width = image.shape[:2]
            
            # Create a copy for annotation
            annotated_image = image.copy()
            
            # Detect dominant colors
            dominant_colors = self._extract_dominant_colors(image, k=5)
            
            # Get color names and create color palette
            color_info = []
            for i, (color, percentage) in enumerate(dominant_colors):
                # Ensure color is a proper tuple with integer values
                b, g, r = [int(c) for c in color]
                rgb_color = (r, g, b)
                hsv = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                
                color_name = self._get_color_name((b, g, r))
                hex_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                
                # Create color info - ensure all values are standard Python types
                color_info.append({
                    'name': color_name,
                    'rgb': [int(r), int(g), int(b)],
                    'hex': hex_code,
                    'percentage': float(round(percentage, 2)),
                    'is_dark': bool(self._is_dark_color(rgb_color)),
                    'is_light': bool(self._is_light_color(rgb_color))
                })
                
                # Draw color palette on the annotated image
                if i < 5:  # Just show top 5 colors
                    start_x = int(width * 0.05)
                    end_x = int(width * 0.25)
                    start_y = int(height * (0.05 + i * 0.06))
                    end_y = int(height * (0.10 + i * 0.06))
                    
                    # Draw color patch - ensure color is tuple with integer values
                    cv2.rectangle(annotated_image, (start_x, start_y), (end_x, end_y), (int(b), int(g), int(r)), -1)
                    
                    # Add text with color name and percentage
                    text_color = (0, 0, 0) if self._is_light_color(rgb_color) else (255, 255, 255)
                    text = f"{color_name} ({percentage:.1f}%)"
                    cv2.putText(annotated_image, text, (end_x + 10, start_y + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
            
            # Store the detected colors
            self.last_detected_colors = color_info
            
            # Analyze color harmony
            color_harmony = self._analyze_color_harmony(dominant_colors)
            
            # Analyze contrast
            contrast_info = self._analyze_contrast(image)
            
            # Add color statistics to image
            self._add_stats_to_image(annotated_image, color_harmony, contrast_info)
            
            # Convert annotated image back to base64
            _, buffer = cv2.imencode('.jpg', annotated_image)
            annotated_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'colors': color_info,
                'dominant_color': color_info[0] if color_info else None,
                'harmony': color_harmony,
                'contrast': contrast_info,
                'annotated_image': annotated_base64
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error detecting colors: {str(e)}",
                'colors': []
            }
    
    def _extract_dominant_colors(self, image, k=5):
        """Extract K dominant colors using K-means clustering"""
        # Reshape the image to be a list of pixels
        pixels = image.reshape((-1, 3)).astype(np.float32)
        
        # Define criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        
        # Apply K-means clustering
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert back to uint8
        centers = np.uint8(centers)
        
        # Count pixels in each cluster and sort by frequency
        unique_labels, counts = np.unique(labels, return_counts=True)
        total_pixels = image.shape[0] * image.shape[1]
        
        # Calculate percentages and create color list
        color_percentages = [(centers[i], (count / total_pixels) * 100) 
                             for i, count in zip(unique_labels, counts)]
        
        # Sort by percentage (descending)
        color_percentages.sort(key=lambda x: x[1], reverse=True)
        
        return color_percentages
    
    def _get_color_name(self, bgr_color):
        """Get the name of a color based on its BGR values"""
        min_distance = float('inf')
        color_name = "unknown"
        
        b, g, r = bgr_color
        
        for name, (min_bgr, max_bgr) in self.color_names.items():
            min_b, min_g, min_r = min_bgr
            max_b, max_g, max_r = max_bgr
            
            if (min_b <= b <= max_b and 
                min_g <= g <= max_g and 
                min_r <= r <= max_r):
                
                # Calculate how central this color is within its range
                b_center = (min_b + max_b) / 2
                g_center = (min_g + max_g) / 2
                r_center = (min_r + max_r) / 2
                
                distance = abs(b - b_center) + abs(g - g_center) + abs(r - r_center)
                
                if distance < min_distance:
                    min_distance = distance
                    color_name = name
                    
        # Special case for grays - any color with small difference between channels
        if max(r, g, b) - min(r, g, b) < 30:
            if r > 200 and g > 200 and b > 200:
                return "white"
            elif r < 50 and g < 50 and b < 50:
                return "black"
            else:
                return "gray"
                
        return color_name
    
    def _is_dark_color(self, rgb):
        """Check if a color is dark (for text contrast)"""
        r, g, b = rgb
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    
    def _is_light_color(self, rgb):
        """Check if a color is light (for text contrast)"""
        return not self._is_dark_color(rgb)
    
    def _analyze_color_harmony(self, color_percentages):
        """Analyze the harmony of the colors in the image"""
        if len(color_percentages) < 2:
            return {
                "type": "monochromatic",
                "description": "Single color palette",
                "score": 5
            }
        
        # Get the top colors
        top_colors = [color for color, _ in color_percentages[:3]]
        
        # Convert BGRs to HSVs
        hsvs = []
        for bgr in top_colors:
            b, g, r = bgr
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            hsvs.append((h * 360, s * 100, v * 100))  # Scale to standard ranges
        
        # Calculate hue differences
        hue_diffs = []
        for i in range(len(hsvs)):
            for j in range(i+1, len(hsvs)):
                diff = abs(hsvs[i][0] - hsvs[j][0])
                # Adjust for circular nature of hue
                if diff > 180:
                    diff = 360 - diff
                hue_diffs.append(diff)
        
        # Determine harmony type
        avg_hue_diff = sum(hue_diffs) / len(hue_diffs) if hue_diffs else 0
        
        # Ensure all values are standard Python types
        if avg_hue_diff < 15:
            return {
                "type": "monochromatic",
                "description": "Variations of a single color",
                "score": int(5)
            }
        elif 15 <= avg_hue_diff <= 45:
            return {
                "type": "analogous",
                "description": "Adjacent colors on the color wheel",
                "score": int(4)
            }
        elif 75 <= avg_hue_diff <= 105:
            return {
                "type": "complementary",
                "description": "Opposite colors on the color wheel",
                "score": int(4)
            }
        elif 165 <= avg_hue_diff <= 180:
            return {
                "type": "triadic",
                "description": "Three colors evenly spaced on the color wheel",
                "score": int(3)
            }
        else:
            return {
                "type": "varied",
                "description": "Mixed color scheme with no specific pattern",
                "score": int(3)
            }
            
    def _analyze_contrast(self, image):
        """Analyze the contrast of the image"""
        # Convert to grayscale for contrast analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate standard deviation as a measure of contrast
        std_dev = np.std(gray)
        
        # Normalize to 0-100 scale
        contrast_score = min(100, std_dev * 0.5)
        
        # Get histogram for distribution analysis
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()  # Normalize
        
        # Calculate entropy (measure of information/detail)
        epsilon = 1e-10  # To avoid log(0)
        entropy = -np.sum(hist * np.log2(hist + epsilon))
        
        # Interpret results
        if contrast_score < 15:
            contrast_type = "low"
            description = "Low contrast - may be difficult to distinguish details"
        elif contrast_score < 40:
            contrast_type = "medium"
            description = "Medium contrast - balanced image"
        else:
            contrast_type = "high"
            description = "High contrast - very distinct light and dark areas"
        
        # Convert numpy types to Python native types for JSON serialization
        return {
            "score": float(round(contrast_score, 2)),
            "type": str(contrast_type),
            "description": str(description),
            "entropy": float(round(entropy, 2))
        }
    
    def _add_stats_to_image(self, image, harmony, contrast):
        """Add color statistics to the image"""
        height, width = image.shape[:2]
        
        # Add a semi-transparent overlay at the bottom
        overlay = image.copy()
        overlay_height = int(height * 0.15)
        cv2.rectangle(overlay, (0, height - overlay_height), (width, height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Add harmony info
        cv2.putText(image, f"Color Harmony: {harmony['type'].title()}", 
                   (20, height - overlay_height + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add contrast info
        cv2.putText(image, f"Contrast: {contrast['type'].title()} ({contrast['score']})", 
                   (20, height - overlay_height + 55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add entropy info
        cv2.putText(image, f"Image Entropy: {contrast['entropy']}", 
                   (width - 250, height - overlay_height + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    def generate_color_palette(self, colors, width=500, height=300, gradient=False):
        """Generate a color palette image from detected colors
        
        Args:
            colors: List of color dictionaries from detect_colors
            width: Width of the output palette
            height: Height of the output palette
            gradient: Whether to use gradients between colors
            
        Returns:
            Base64 encoded palette image
        """
        try:
            # Create a new image
            palette = np.ones((height, width, 3), dtype=np.uint8) * 255
            
            if not colors:
                return None
                
            # Extract RGB values
            rgb_colors = [color['rgb'] for color in colors]
            
            if gradient and len(rgb_colors) > 1:
                # Create a gradient palette
                for x in range(width):
                    # Determine which color segment this pixel belongs to
                    segment_width = width / (len(rgb_colors) - 1)
                    segment = int(x / segment_width)
                    
                    # Handle edge case for the last pixel
                    if segment >= len(rgb_colors) - 1:
                        segment = len(rgb_colors) - 2
                        
                    # Calculate interpolation factor
                    factor = (x - segment * segment_width) / segment_width
                    
                    # Get colors to interpolate between
                    color1 = np.array(rgb_colors[segment])
                    color2 = np.array(rgb_colors[segment + 1])
                    
                    # Interpolate color
                    interpolated = color1 * (1 - factor) + color2 * factor
                    interpolated = interpolated.astype(np.uint8)
                    
                    # Draw vertical line of this color
                    palette[:, x] = interpolated[::-1]  # Convert RGB to BGR for OpenCV
            else:
                # Create a block palette
                num_colors = len(rgb_colors)
                block_width = width // num_colors
                
                for i, color in enumerate(rgb_colors):
                    # Convert RGB to BGR for OpenCV
                    bgr_color = (color[2], color[1], color[0])
                    
                    # Calculate block position
                    start_x = i * block_width
                    end_x = (i + 1) * block_width if i < num_colors - 1 else width
                    
                    # Draw color block
                    palette[:, start_x:end_x] = bgr_color
            
            # Convert to base64
            _, buffer = cv2.imencode('.png', palette)
            palette_base64 = 'data:image/png;base64,' + base64.b64encode(buffer).decode('utf-8')
            
            return palette_base64
            
        except Exception as e:
            print(f"Error generating color palette: {e}")
            return None
    
    def get_last_detected_colors(self):
        """Return the last detected colors"""
        return self.last_detected_colors

# Create singleton instance
color_detection_service = ColorDetectionService() 