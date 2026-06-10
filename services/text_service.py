import os
import pytesseract
import cv2
import numpy as np
from PIL import Image
import base64
import re
import sys
import platform

class TextRecognitionService:
    def __init__(self):
        self.tesseract_installed = False
        self.tesseract_cmd = self._get_tesseract_cmd()
        
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            self.tesseract_installed = True
            print(f"Tesseract OCR found at: {self.tesseract_cmd}")
        else:
            print("WARNING: Tesseract OCR not found. Text recognition will not work properly.")
            print(self._get_installation_instructions())
        
        self.last_recognition = {
            'text': '',
            'confidence': 0
        }
    
    def _get_tesseract_cmd(self):
        """Try to find Tesseract executable on common paths"""
        # Check if already in PATH
        try:
            # Try a basic test with pytesseract
            pytesseract.get_tesseract_version()
            print("Found Tesseract in PATH")
            return pytesseract.pytesseract.tesseract_cmd
        except Exception as e:
            print(f"Tesseract not in PATH: {e}")
            pass
        
        # Look for common installation paths
        system = platform.system()
        
        if system == 'Windows':
            common_paths = [
                # Standard install locations
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
                # Windows Store installation
                os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Tesseract-OCR\tesseract.exe'),
                # User apps locations
                os.path.join(os.environ.get('APPDATA', ''), r'Tesseract-OCR\tesseract.exe'),
                # Additional UB Mannheim installer locations
                r'C:\Users\Public\Tesseract-OCR\tesseract.exe',
                # Common custom install paths
                r'D:\Tesseract-OCR\tesseract.exe',
                r'E:\Tesseract-OCR\tesseract.exe',
            ]
            
            # Look for Program Files directories with Tesseract in the name
            program_files = os.environ.get('ProgramFiles', r'C:\Program Files')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')
            
            try:
                # Try to find any directory with 'tesseract' in the name in Program Files
                for pf_dir in [program_files, program_files_x86]:
                    if os.path.exists(pf_dir):
                        for dir_name in os.listdir(pf_dir):
                            if 'tesseract' in dir_name.lower():
                                # Check potential executable locations
                                potential_exe = os.path.join(pf_dir, dir_name, 'tesseract.exe')
                                common_paths.append(potential_exe)
            except Exception as e:
                print(f"Error scanning Program Files: {e}")
        
        elif system == 'Darwin':  # macOS
            common_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                '/opt/local/bin/tesseract'
            ]
        else:  # Linux and others
            common_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
                '/opt/tesseract/bin/tesseract'
            ]
        
        # Check all potential paths
        for path in common_paths:
            if os.path.exists(path):
                print(f"Found Tesseract at: {path}")
                return path
        
        # Manual check - look for tesseract.exe in current directory and subdirectories
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for root, dirs, files in os.walk(base_dir):
                if 'tesseract.exe' in files:
                    tesseract_path = os.path.join(root, 'tesseract.exe')
                    print(f"Found Tesseract in local directory: {tesseract_path}")
                    return tesseract_path
        except Exception as e:
            print(f"Error scanning local directories: {e}")
                
        # Try scanning common drives on Windows
        if system == 'Windows':
            try:
                for drive in ['C:', 'D:', 'E:']:
                    print(f"Scanning {drive} for Tesseract...")
                    # Look for tesseract-ocr folder in root directory
                    tesseract_dir = os.path.join(drive, 'Tesseract-OCR')
                    if os.path.exists(tesseract_dir):
                        tesseract_exe = os.path.join(tesseract_dir, 'tesseract.exe')
                        if os.path.exists(tesseract_exe):
                            print(f"Found Tesseract at: {tesseract_exe}")
                            return tesseract_exe
            except Exception as e:
                print(f"Error scanning drives: {e}")
        
        print("Tesseract not found in any expected location.")
        return None
    
    def _get_installation_instructions(self):
        """Return installation instructions based on the platform"""
        system = platform.system()
        
        if system == "Windows":
            return """
Tesseract OCR Installation Instructions (Windows):
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and follow the instructions
3. Make sure to add Tesseract to your PATH during installation
4. Restart the application after installation
"""
        elif system == "Darwin":  # macOS
            return """
Tesseract OCR Installation Instructions (macOS):
1. Install Homebrew if not already installed: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2. Install Tesseract: brew install tesseract
3. Restart the application after installation
"""
        else:  # Linux
            return """
Tesseract OCR Installation Instructions (Linux):
1. Install Tesseract: sudo apt-get install tesseract-ocr
   (or use your distribution's package manager)
2. Restart the application after installation
"""
    
    def recognize_text(self, image_data):
        """Recognize text from base64 image data"""
        try:
            if not self.tesseract_installed:
                # Provide detailed error information
                possible_install_locations = ""
                if platform.system() == 'Windows':
                    possible_install_locations = """
                    <p>Common Windows installation paths:</p>
                    <ul>
                        <li>C:\\Program Files\\Tesseract-OCR\\tesseract.exe</li>
                        <li>C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe</li>
                        <li>C:\\Tesseract-OCR\\tesseract.exe</li>
                    </ul>
                    """

                return {
                    'success': False,
                    'message': f"""
                    <p>Tesseract OCR is not installed or not found in the system PATH.</p>
                    {possible_install_locations}
                    <p>After installing, you may need to <strong>restart the application</strong>.</p>
                    <p>You can download Tesseract OCR from <a href="https://github.com/UB-Mannheim/tesseract/releases" target="_blank">GitHub (UB-Mannheim)</a>.</p>
                    <p>During installation, make sure to check the option to <strong>add Tesseract to your PATH</strong>.</p>
                    """ + self._get_installation_instructions(),
                    'confidence': 0,
                    'tesseract_missing': True
                }
            
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
            
            # Get dimensions of image for diagnostic info
            height, width = image.shape[:2]
            print(f"Processing image: {width}x{height} pixels")
            
            # Get all preprocessed image variants
            preprocessed_variants = self._get_all_preprocessed_variants(image)
            
            # Try OCR on each preprocessed image using different configs
            ocr_configs = [
                {"name": "default", "config": "--psm 3"},  # Auto page segmentation
                {"name": "single_block", "config": "--psm 6"},  # Single block of text
                {"name": "single_line", "config": "--psm 7"},  # Single line
                {"name": "multiple_blocks", "config": "--psm 4"},  # Multiple blocks of text
                {"name": "sparse", "config": "--psm 11"}  # Sparse text
            ]
            
            best_result = None
            best_confidence = -1
            best_preprocessing = None
            
            # For each preprocessing method, try each OCR config
            for prep_name, preprocessed in preprocessed_variants:
                for config in ocr_configs:
                    try:
                        print(f"Trying OCR with preprocessing: {prep_name}, config: {config['name']}")
                        
                        # Get OCR data with current config
                        ocr_data = pytesseract.image_to_data(
                            preprocessed, 
                            output_type=pytesseract.Output.DICT,
                            config=config["config"]
                        )
                        
                        # Extract text and confidence
                        text_parts = []
                        confidences = []
                        
                        for i in range(len(ocr_data['text'])):
                            if int(ocr_data['conf'][i]) > 0:  # Filter out low confidence results
                                text = ocr_data['text'][i].strip()
                                conf = int(ocr_data['conf'][i])
                                
                                if text:
                                    text_parts.append(text)
                                    confidences.append(conf)
                        
                        if text_parts:
                            full_text = ' '.join(text_parts)
                            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                            
                            # Convert confidence to a value between 0 and 1 (Tesseract gives 0-100)
                            normalized_confidence = avg_confidence / 100.0
                            
                            # If this combination gave better results
                            if avg_confidence > best_confidence:
                                best_confidence = avg_confidence
                                best_preprocessing = prep_name
                                best_result = {
                                    "text": full_text,
                                    "confidence": normalized_confidence,
                                    "config": config["name"],
                                    "preprocessing": prep_name
                                }
                    
                    except Exception as e:
                        print(f"Error with OCR config {config['name']} and preprocessing {prep_name}: {e}")
                        continue
            
            # If we found any usable results
            if best_result:
                # Clean up extra spaces and newlines
                cleaned_text = re.sub(r'\s+', ' ', best_result["text"]).strip()
                
                self.last_recognition = {
                    'text': cleaned_text,
                    'confidence': best_result["confidence"]
                }
                
                print(f"Best OCR result using preprocessing: {best_preprocessing}, config: {best_result['config']}, with confidence {best_confidence:.2f}% (normalized: {best_result['confidence']:.2f})")
                
                # Create a detailed response with diagnostic info
                return {
                    'success': True,
                    'text': cleaned_text,
                    'confidence': best_result["confidence"],
                    'config_used': best_result["config"],
                    'preprocessing_used': best_preprocessing,
                    'image_size': f"{width}x{height}",
                    'using_real_ocr': True
                }
            else:
                return {
                    'success': False,
                    'message': 'No text detected in image. Try a clearer image with better lighting and contrast.',
                    'confidence': 0
                }
        
        except Exception as e:
            print(f"Error recognizing text: {e}")
            
            # Check if the error is related to Tesseract not being found
            error_msg = str(e).lower()
            if "tesseract is not installed" in error_msg or "tesseract not found" in error_msg:
                return {
                    'success': False,
                    'message': f"<p>Tesseract OCR error: {str(e)}</p><p>Please ensure Tesseract is properly installed.</p>",
                    'confidence': 0,
                    'tesseract_missing': True
                }
            
            return {
                'success': False,
                'message': f"Error processing image: {str(e)}",
                'confidence': 0
            }
    
    def _get_all_preprocessed_variants(self, image):
        """Create and return all preprocessed image variants"""
        # Create multiple preprocessing variants
        preprocessed_images = []
        
        # Original grayscale conversion
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        preprocessed_images.append(("gray", gray))
        
        # Apply noise reduction
        denoise = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # 1. Otsu's thresholding
        _, otsu = cv2.threshold(denoise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_images.append(("otsu", otsu))
        
        # 2. Adaptive thresholding
        adaptive = cv2.adaptiveThreshold(
            denoise, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 
            2
        )
        preprocessed_images.append(("adaptive", adaptive))
        
        # 3. Apply unsharp masking for sharpening
        blur = cv2.GaussianBlur(denoise, (0, 0), 3)
        sharp = cv2.addWeighted(denoise, 1.5, blur, -0.5, 0)
        _, sharp_thresh = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_images.append(("sharp", sharp_thresh))
        
        # 4. High contrast adjustment
        # Apply histogram equalization to improve contrast
        equ = cv2.equalizeHist(denoise)
        _, high_contrast = cv2.threshold(equ, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_images.append(("high_contrast", high_contrast))
        
        # 5. Edge enhancement
        # Use Canny edge detection with dilation to enhance text edges
        edges = cv2.Canny(denoise, 100, 200)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        # Invert the edges for better OCR
        inverted_edges = cv2.bitwise_not(dilated_edges)
        preprocessed_images.append(("edges", inverted_edges))
        
        # 6. Morphological operations
        # Apply morphological operations to enhance text structure
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, kernel)
        preprocessed_images.append(("morph", morph))
        
        # 7. Dilated version for connected components
        dilated = cv2.dilate(otsu, kernel, iterations=1)
        preprocessed_images.append(("dilated", dilated))
        
        # 8. Inverted version (sometimes white text on black background works better)
        inverted = cv2.bitwise_not(otsu)
        preprocessed_images.append(("inverted", inverted))
        
        # 9. Resize for better recognition (sometimes larger text is easier to recognize)
        # Scale the image by a factor of 2
        height, width = gray.shape
        scaled = cv2.resize(otsu, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        preprocessed_images.append(("scaled", scaled))
        
        # 10. Special text enhancement technique
        # This combination has shown good results for text clarity
        # First apply bilateral filter to smooth while preserving edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        # Then apply adaptive threshold to get binary image
        text_enhanced = cv2.adaptiveThreshold(
            bilateral,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,  # Larger block size
            5    # Higher constant subtracted from mean
        )
        preprocessed_images.append(("text_enhanced", text_enhanced))
        
        # 11. Super-resolution technique for text (simulate)
        # This is a simplified version - in production you might use a proper SR algorithm
        sr_img = cv2.GaussianBlur(gray, (0, 0), 3)
        sr_img = cv2.addWeighted(gray, 1.5, sr_img, -0.5, 0)
        _, sr_thresh = cv2.threshold(sr_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Scale up for higher precision
        sr_scaled = cv2.resize(sr_thresh, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        preprocessed_images.append(("super_res", sr_scaled))
        
        # Return all variants
        return preprocessed_images
    
    def recognize_text_with_method(self, image, method="default"):
        """Try different OCR approaches and parameters"""
        try:
            if method == "default":
                # Default pytesseract OCR
                return pytesseract.image_to_string(image)
            elif method == "digits":
                # Optimized for digits
                return pytesseract.image_to_string(image, config='--psm 6 outputbase digits')
            elif method == "single_line":
                # Optimized for a single line of text
                return pytesseract.image_to_string(image, config='--psm 7')
            elif method == "multiple_lines":
                # Optimized for multiple lines of text
                return pytesseract.image_to_string(image, config='--psm 6')
            else:
                return pytesseract.image_to_string(image)
        except Exception as e:
            print(f"Error with OCR method {method}: {e}")
            return ""
    
    def get_last_recognition(self):
        """Return the last recognized text"""
        return self.last_recognition

# Create singleton instance
text_recognition_service = TextRecognitionService() 