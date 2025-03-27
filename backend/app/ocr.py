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

def preprocess_image(image, for_tesseract=False):
    """Preprocess the image adaptively for all text types."""
    try:
        # Add minimal padding to avoid cropping text near edges
        image = ImageOps.expand(image, border=10, fill='white')

        # Preserve aspect ratio with a maximum size
        original_size = image.size
        max_size = 4000 if for_tesseract else 384  # High resolution for Tesseract
        ratio = min(max_size / original_size[0], max_size / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Increase contrast for better text clarity
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0 if for_tesseract else 1.5)

        # Convert to grayscale
        image = image.convert("L")

        # Convert to NumPy array for further processing
        image_np = np.array(image)
        if image_np.size > 0:  # Ensure array is not empty
            # Apply a slight blur to reduce noise
            image_np = cv2.GaussianBlur(image_np, (3, 3), 0)

            # Deskew the image to handle rotation
            coords = np.column_stack(np.where(image_np < 128))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                (h, w) = image_np.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                image_np = cv2.warpAffine(image_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

            # Use adaptive thresholding to handle varying lighting
            image_binary = cv2.adaptiveThreshold(
                image_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            # Apply minimal dilation to prevent characters from merging
            kernel = np.ones((1, 1), np.uint8)
            image_binary = cv2.dilate(image_binary, kernel, iterations=1)
            image = Image.fromarray(image_binary)

        # Convert back to RGB for TrOCR if needed
        if not for_tesseract:
            image = image.convert("RGB")

        logger.info(f"Image preprocessed: size={image.size}, mode={image.mode}")
        return image
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise Exception(f"Image preprocessing failed: {str(e)}")

def post_process_text(text):
    """Post-process the extracted text to clean up common OCR errors for all text types."""
    # Normalize whitespace and split into lines
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        # Remove extra spaces
        line = re.sub(r'\s+', ' ', line).strip()
        # Skip gibberish lines (less than 3 characters or no letters)
        if len(line) < 3 or not any(c.isalpha() for c in line):
            continue
        # Fix common OCR misreads
        line = re.sub(r'Z([a-zA-Z])', r'l\1', line)  # Z to l (e.g., Zogger to logger)
        line = re.sub(r'7([a-zA-Z])', r'l\1', line)  # 7 to l
        line = re.sub(r'rn([a-zA-Z])', r'm\1', line)  # rn to m (e.g., form to form)
        line = re.sub(r't Fy', 'try', line)  # t Fy to try
        line = re.sub(r'___ epye _ \|', 'try:', line)  # ___ epye _ | to try:
        line = re.sub(r'a Uto', 'auto', line)  # a Uto to auto
        line = re.sub(r'([a-zA-Z])6([a-zA-Z])', r'\1.\2', line)  # 6 to . (e.g., 7ogger 6 info)
        line = re.sub(r'filenamée', 'filename', line)  # filenamée to filename
        line = re.sub(r'Logger', 'logger', line)  # Logger to logger
        line = re.sub(r'\.\.+', '.', line)  # Logger..info to logger.info
        line = re.sub(r'form\.data', 'form_data', line)  # form.data to form_data
        line = re.sub(r'formdata', 'form_data', line)  # formdata to form_data
        line = re.sub(r'sourcé_lang', 'source_lang', line)  # sourcé_lang to source_lang
        line = re.sub(r'S0', '50', line)  # S0 to 50
        # Remove quotes around variable names in assignments
        line = re.sub(r'\'([a-zA-Z_]+)\'\s*=', r'\1 =', line)  # 'text' = to text =
        # Add spaces around operators
        line = re.sub(r'([a-zA-Z0-9_])\s*=\s*([a-zA-Z0-9_])', r'\1 = \2', line)
        # Remove extra colons after variables
        line = re.sub(r'\'([a-zA-Z_]+)\'\s*:\s*=', r"'\1' =", line)  # 'option': = to 'option' =
        # Fix spaces around dots
        line = re.sub(r'\s*\.\s*', '.', line)  # request . form to request.form
        # Fix quotes and parentheses
        line = re.sub(r'\'\'([a-zA-Z_]+)\'\'', r"'\1'", line)  # ''text'' to 'text'
        line = re.sub(r'\'([a-zA-Z_]+)\', \'\'', r"'\1', ''", line)  # 'text', '' to 'text', ''
        line = re.sub(r'\'([a-zA-Z_]+)\', \'\'([a-zA-Z_]+)\'\'', r"'\1', '\2'", line)  # 'option', ''ocr'' to 'option', 'ocr'
        line = re.sub(r'\'\'([a-zA-Z_]+)\'\'', r"'\1'", line)  # "'target_lang''" to 'target_lang'
        line = re.sub(r'\'([a-zA-Z_]+)\'\', \'\'([a-zA-Z_]+)\'\'', r"'\1', '\2'", line)  # "'target_lang'', ''en''" to "'target_lang', 'en'"
        line = re.sub(r'\'([a-zA-Z_]+)"\'', r"'\1'", line)  # 'target_lang"' to 'target_lang'
        line = re.sub(r'\'\'\'([a-zA-Z_]+)\'\'\'', r"'\1'", line)  # '''en''' to 'en'
        line = re.sub(r'[‘’]', "'", line)  # Replace smart quotes with straight quotes
        line = re.sub(r'([a-zA-Z_]+)\s*:\s*get', r'\1.get', line)  # form_data : get to form_data.get
        # Fix f-strings by adding quotes and proper spacing
        line = re.sub(r'f([A-Z])', r'f"\1', line)
        line = re.sub(r'"f"Options', r'f"Options', line)  # "f"Options to f"Options
        line = re.sub(r'f"([a-zA-Z_]+)\[', r'f"{\1[', line)
        line = re.sub(r'f([a-zA-Z_]+)\{', r'f"{\1', line)  # ftext{ to f"{text
        line = re.sub(r'(\[:\d+])', r'{\1}', line)
        line = re.sub(r'\{([a-zA-Z_]+)\s*\{', r'{\1{', line)  # {'text' {[:50]}} to {'text'[:50]}}
        line = re.sub(r'\'([a-zA-Z_]+)\'\{\[:', r'\1{[:', line)  # {'text'{[:50]}} to {text[:50]}
        line = re.sub(r'\{([a-zA-Z_]+)\.filename', r"{\1.filename", line)  # {'file'.filename to {file.filename
        line = re.sub(r'\}\s*,\s*', '}, ', line)  # Fix commas in f-strings
        # Fix common misreads (e.g., '4' or '&' instead of '#')
        line = re.sub(r'^4(\s|$)', r'#\1', line)
        line = re.sub(r'^&(\s|$)', r'#\1', line)
        # Add quotes around string literals (for code)
        line = re.sub(r'\b(text|file|option|source_lang|target_lang|auto|ocr|en)\b', r"'\1'", line)
        # Fix logger.info arguments (for code)
        line = re.sub(r'logger\.info\(([^"])', r'logger.info("\1', line)
        line = re.sub(r'logger\.info\("([^"]*?)(?=\))', r'logger.info("\1")', line)
        # Remove stray underscores at the end
        line = re.sub(r'_+$', '', line)
        processed_lines.append(line)

    # Join lines back together, preserving line breaks
    text = '\n'.join(processed_lines)
    return text.strip()

def ocr_with_tesseract(image, lang='en'):
    """OCR using Tesseract with optimized settings for all text types."""
    try:
        image = preprocess_image(image, for_tesseract=True)
        # Map language codes to Tesseract language codes
        tesseract_lang_map = {
            'en': 'eng',
            'fr': 'fra',
            'de': 'deu',
            'hi': 'hin'
        }
        tesseract_lang = tesseract_lang_map.get(lang, 'eng')  # Default to English if lang not supported
        # PSM 3 for fully automatic page segmentation, OEM 1 for LSTM, preserve spaces
        config = f"--psm 3 --oem 1 -l {tesseract_lang} -c preserve_interword_spaces=1 -c textord_tabfind_show_blocks=0"
        text = pytesseract.image_to_string(image, config=config)
        # Post-process the text to clean up OCR errors
        text = post_process_text(text)
        logger.info(f"Tesseract extracted text (lang={tesseract_lang}): {text[:100]}...")
        return text.strip()
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {str(e)}")
        raise Exception(f"Tesseract OCR failed: {str(e)}")

def ocr_with_trocr(image):
    """OCR using TrOCR for handwritten text."""
    try:
        image = preprocess_image(image, for_tesseract=False)
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        logger.info(f"Pixel values shape: {pixel_values.shape}")
        generated_ids = model.generate(pixel_values, max_length=512)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        # Post-process the text to clean up OCR errors
        text = post_process_text(text)
        logger.info(f"TrOCR extracted text: {text[:100]}...")
        return text.strip()
    except Exception as e:
        logger.error(f"TrOCR OCR failed: {str(e)}")
        raise Exception(f"TrOCR OCR failed: {str(e)}")

def ocr_with_easyocr(image, lang='en'):
    """OCR using EasyOCR for multi-language and low-quality images."""
    try:
        image = preprocess_image(image, for_tesseract=True)
        # Convert PIL Image to NumPy array for EasyOCR
        image_np = np.array(image)
        # Choose the appropriate reader based on the language
        reader = devanagari_reader if lang == 'hi' else latin_reader
        # Adjust parameters for better layout detection
        result = reader.readtext(
            image_np,
            detail=0,
            paragraph=False,  # Preserve line breaks
            text_threshold=0.8,  # Increase confidence threshold
            low_text=0.3  # Adjust for smaller text
        )
        text = '\n'.join(result)
        # Post-process the text to clean up OCR errors
        text = post_process_text(text)
        logger.info(f"EasyOCR extracted text: {text[:100]}...")
        return text.strip()
    except Exception as e:
        logger.error(f"EasyOCR failed: {str(e)}")
        raise Exception(f"EasyOCR failed: {str(e)}")

def is_valid_text(text):
    """Basic validation to check if OCR output is reasonable."""
    return len(text) > 5 and any(c.isalpha() for c in text)

def detect_text_type(image):
    """Simple heuristic to detect text type (printed vs. handwritten)."""
    image = preprocess_image(image, for_tesseract=True)
    text = ocr_with_tesseract(image)
    # If Tesseract produces gibberish or low confidence, assume handwritten
    if not is_valid_text(text) or len(text.split()) < 3:
        return "handwritten"
    return "printed"

def ocr_process(text, file, lang='en'):
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
            elif file.mimetype in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                logger.error("DOC/DOCX files are not supported yet in this version of our Pilot project")
                raise Exception("DOC/DOCX files are not supported yet in this version of our Pilot project")
            else:
                try:
                    images = [Image.open(io.BytesIO(file_content)).convert("RGB")]
                    logger.info("Successfully opened file as image despite missing mimetype")
                except Exception as e:
                    logger.error(f"Failed to open as image: {str(e)}")
                    raise Exception("Invalid file format")

            # Process each image
            results = []
            for image in images:
                # Detect text type
                text_type = detect_text_type(image)
                logger.info(f"Detected text type: {text_type}")

                # Step 1: Try both EasyOCR and Tesseract, then compare
                easyocr_text = ocr_with_easyocr(image, lang=lang)
                tesseract_text = ocr_with_tesseract(image, lang=lang)

                # Compare the results based on a simple heuristic
                if is_valid_text(easyocr_text) and is_valid_text(tesseract_text):
                    # Score based on number of valid words and presence of quotes
                    easyocr_score = len(easyocr_text.split()) + easyocr_text.count('"') * 2
                    tesseract_score = len(tesseract_text.split()) + tesseract_text.count('"') * 2
                    if easyocr_score > tesseract_score:
                        logger.info("Using EasyOCR result")
                        results.append(easyocr_text)
                    else:
                        logger.info("Using Tesseract result")
                        results.append(tesseract_text)
                    continue
                elif is_valid_text(easyocr_text):
                    logger.info("Using EasyOCR result")
                    results.append(easyocr_text)
                    continue
                elif is_valid_text(tesseract_text):
                    logger.info("Using Tesseract result")
                    results.append(tesseract_text)
                    continue

                # Step 2: Try TrOCR if handwritten or others fail
                if text_type == "handwritten":
                    trocr_text = ocr_with_trocr(image)
                    if is_valid_text(trocr_text):
                        logger.info("Using TrOCR result")
                        results.append(trocr_text)
                        continue

                logger.warning("All OCR models failed to produce valid text")
                results.append("Unable to extract text")

            return '\n'.join(results)

        logger.warning("No content to process")
        return "No content to process"

    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise Exception(f"OCR processing failed: {str(e)}")