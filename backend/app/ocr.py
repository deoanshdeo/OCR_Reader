from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageEnhance, ImageOps
import io
import logging
import pytesseract
import easyocr
from pdf2image import convert_from_bytes
import os
import numpy as np
import cv2
import re

# Specify Tesseract path explicitly
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the TrOCR model and processor for printed text, force CPU usage
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed', use_fast=True)
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed').to('cpu')

# Initialize two EasyOCR readers to handle language compatibility
latin_reader = easyocr.Reader(['en', 'fr', 'de'], gpu=False)  # For Latin-script languages
devanagari_reader = easyocr.Reader(['hi', 'en'], gpu=False)  # For Devanagari-script languages (Hindi + English)

def is_code_image(image):
    """Detect if the image likely contains code based on patterns."""
    try:
        # Preprocess lightly for detection
        image = preprocess_image(image, for_tesseract=True)
        text = pytesseract.image_to_string(image, config="--psm 6 --oem 3 -l eng")
        # Look for code-like patterns
        code_indicators = ['def ', 'if ', 'try:', '# ', ' = ', '(', ')', '{', '}']
        is_code = any(indicator in text for indicator in code_indicators)
        logger.info(f"Code detection result: {is_code}")
        return is_code
    except Exception as e:
        logger.warning(f"Code detection failed: {str(e)}, defaulting to non-code")
        return False

def preprocess_image(image, for_tesseract=False):
    """Advanced image preprocessing for OCR, optimized for non-code images."""
    try:
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Add minimal padding to avoid cropping text near edges
        image = ImageOps.expand(image, border=10, fill='white')

        # Preserve aspect ratio with a maximum size
        original_size = image.size
        max_size = 4000 if for_tesseract else 384
        ratio = min(max_size / original_size[0], max_size / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to NumPy array for OpenCV processing
        image_np = np.array(image)
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

        # Use adaptive thresholding for better handling of varying lighting
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Denoise using bilateral filter to preserve edges
        denoised = cv2.bilateralFilter(thresh, 9, 75, 75)

        # Sharpen image
        sharp_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, sharp_kernel)

        # Convert back to PIL Image
        processed_image = Image.fromarray(sharpened)

        # Increase contrast if needed
        enhancer = ImageEnhance.Contrast(processed_image)
        processed_image = enhancer.enhance(1.5)

        logger.info(f"Image preprocessed: size={processed_image.size}")
        return processed_image

    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return image  # Return original image if preprocessing fails

def preprocess_image_for_code(image):
    """Minimal preprocessing for code images to preserve details."""
    try:
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Add minimal padding to avoid cropping text near edges
        image = ImageOps.expand(image, border=10, fill='white')

        # Increase resolution for better character recognition
        original_size = image.size
        max_size = 4000  # Higher resolution for code images
        ratio = min(max_size / original_size[0], max_size / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to NumPy array for OpenCV processing
        image_np = np.array(image)
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

        # Use simple thresholding to preserve character details
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # Convert back to PIL Image
        processed_image = Image.fromarray(thresh)

        logger.info(f"Code image preprocessed: size={processed_image.size}")
        return processed_image

    except Exception as e:
        logger.error(f"Code image preprocessing failed: {str(e)}")
        return image

def post_process_text(text):
    """Improved text post-processing for non-code text with minimal intervention."""
    try:
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove any non-printable characters
        text = ''.join(char for char in text if char.isprintable())

        # Remove extremely short lines or lines with no meaningful content
        lines = text.split('\n')
        filtered_lines = [
            line.strip() for line in lines
            if len(line.strip()) > 2 and sum(c.isalnum() for c in line) > 1
        ]

        return '\n'.join(filtered_lines)
    except Exception as e:
        logger.error(f"Text post-processing failed: {str(e)}")
        return text

def post_process_code(text):
    """Post-processing for code to preserve formatting and fix common OCR errors."""
    try:
        # Normalize line endings
        text = text.replace('\r\n', '\n')

        # Preserve leading whitespace (indentation)
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            # Preserve the original leading whitespace
            leading_whitespace = len(line) - len(line.lstrip())
            stripped_line = line.strip()

            if not stripped_line:
                processed_lines.append(line)  # Preserve empty lines
                continue

            # Fix spacing around dots (e.g., "logger. info" -> "logger.info")
            stripped_line = re.sub(r'\.\s+', '.', stripped_line)

            # Replace smart quotes with straight quotes
            stripped_line = stripped_line.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')

            # Fix misplaced comment symbols (e.g., 'info(#"Options' -> 'info(f"Options')
            if '#' in stripped_line and not stripped_line.startswith('#'):
                # Check if '#' is inside a string (simplified check)
                parts = stripped_line.split('"')
                if len(parts) > 1:  # Likely a string
                    for i in range(len(parts)):
                        if '#' in parts[i] and i % 2 == 1:  # Inside a string
                            parts[i] = parts[i].replace('#', 'f')  # Replace with 'f' (likely f-string)
                    stripped_line = '"'.join(parts)

            # Reconstruct the line with preserved indentation
            processed_line = ' ' * leading_whitespace + stripped_line
            processed_lines.append(processed_line)

        # Join the lines back together
        text = '\n'.join(processed_lines).strip()

        # Ensure underscores are preserved (e.g., "formdata" -> "form_data")
        text = re.sub(r'formdata', 'form_data', text)

        return text
    except Exception as e:
        logger.error(f"Code post-processing failed: {str(e)}")
        return text

def ocr_with_tesseract(image, lang='en'):
    """OCR using Tesseract with optimized settings."""
    try:
        # Preprocess for Tesseract
        image = preprocess_image(image, for_tesseract=True)

        # Map language codes to Tesseract language codes
        tesseract_lang_map = {
            'en': 'eng',
            'fr': 'fra',
            'de': 'deu',
            'hi': 'hin'
        }
        tesseract_lang = tesseract_lang_map.get(lang, 'eng')

        # Tesseract configuration
        config = f"--psm 6 --oem 3 -l {tesseract_lang}"
        text = pytesseract.image_to_string(image, config=config)

        # Post-process the text
        text = post_process_text(text)

        logger.info(f"Tesseract extracted text (lang={tesseract_lang}): {text[:100]}...")
        return text
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {str(e)}")
        return ""

def ocr_with_easyocr(image, lang='en'):
    """OCR using EasyOCR for multi-language support."""
    try:
        # Preprocess for EasyOCR
        image = preprocess_image(image, for_tesseract=True)
        image_np = np.array(image)

        # Choose appropriate reader
        reader = devanagari_reader if lang == 'hi' else latin_reader

        # Extract text with improved parameters
        result = reader.readtext(
            image_np,
            detail=0,  # Only return text
            paragraph=True,  # Try to maintain text layout
            text_threshold=0.7,  # Moderate confidence threshold
            low_text=0.4
        )

        # Join results and post-process
        text = ' '.join(result) if result else ""
        text = post_process_text(text)

        logger.info(f"EasyOCR extracted text: {text[:100]}...")
        return text
    except Exception as e:
        logger.error(f"EasyOCR failed: {str(e)}")
        return ""

def ocr_with_trocr(image):
    """OCR using TrOCR for printed text."""
    try:
        # Preprocess for TrOCR
        image = preprocess_image(image, for_tesseract=False)

        # Prepare image for model
        pixel_values = processor(images=image, return_tensors="pt").pixel_values

        # Generate text
        generated_ids = model.generate(pixel_values, max_length=512)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # Post-process the text
        text = post_process_text(text)

        logger.info(f"TrOCR extracted text: {text[:100]}...")
        return text
    except Exception as e:
        logger.error(f"TrOCR OCR failed: {str(e)}")
        return ""

def ocr_for_code(image):
    """OCR pipeline specifically for code images."""
    try:
        # Preprocess minimally for code
        image = preprocess_image_for_code(image)

        # Use Tesseract with a configuration optimized for code
        # Try --psm 1 (single block of text) to better handle full lines
        config = "--psm 1 --oem 3 -l eng"
        text = pytesseract.image_to_string(image, config=config)

        # Post-process minimally to preserve code formatting
        text = post_process_code(text)

        logger.info(f"Code OCR extracted text: {text[:100]}...")
        return text
    except Exception as e:
        logger.error(f"Code OCR failed: {str(e)}")
        return ""

def merge_ocr_results(results):
    """Intelligently merge multiple OCR results."""
    # Remove empty results
    valid_results = [r for r in results if r.strip()]

    if not valid_results:
        return ""

    # If only one result, return it
    if len(valid_results) == 1:
        return valid_results[0]

    # Strategy: Combine unique parts from different results
    # Prefer longer, more meaningful results
    merged_text = max(valid_results, key=lambda x: len(x.split()))

    logger.info(f"Merged OCR result: {merged_text[:100]}...")
    return merged_text

def ocr_process(text, file, lang='en'):
    """Robust OCR processing with multiple fallback methods."""
    try:
        # If text is provided, return it as-is
        if text:
            logger.info("Processing provided text")
            return text

        # If a file is provided, process it
        if file:
            logger.info(f"Processing file with mimetype: {file.mimetype}")
            file_content = file.read()
            images = []
            # Handle different file types
            if file.mimetype and file.mimetype.startswith('image'):
                images = [Image.open(io.BytesIO(file_content)).convert("RGB")]
            elif file.mimetype == 'application/pdf':
                images = convert_from_bytes(file_content)
            else:
                try:
                    images = [Image.open(io.BytesIO(file_content)).convert("RGB")]
                    logger.info("Successfully opened file as image")
                except Exception as e:
                    logger.error(f"Failed to open file: {str(e)}")
                    return "Unable to process file"

            # Process each image and collect results
            results = []
            for image in images:
                # Detect if the image contains code
                if is_code_image(image):
                    logger.info("Detected code in image")
                    result = ocr_for_code(image)
                    results.append(result)
                else:
                    logger.info("Processing as non-code image")
                    # Multiple OCR methods for non-code images
                    ocr_methods = [
                        lambda img: ocr_with_tesseract(img, lang),
                        lambda img: ocr_with_easyocr(img, lang),
                        lambda img: ocr_with_trocr(img)
                    ]

                    # Try each OCR method
                    image_results = []
                    for method in ocr_methods:
                        try:
                            result = method(image)
                            if result:
                                image_results.append(result)
                                logger.info(f"OCR method result: {result[:50]}...")
                        except Exception as e:
                            logger.warning(f"OCR method failed: {str(e)}")

                    # Merge results for this image
                    if image_results:
                        results.append(merge_ocr_results(image_results))

            # Combine results from multiple images
            final_text = '\n'.join(results) if results else "No text extracted"

            logger.info(f"Final OCR result length: {len(final_text)}")
            return final_text

        logger.warning("No content to process")
        return "No content to process"

    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        return f"OCR processing error: {str(e)}"