from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageEnhance, ImageOps
import io
import logging
import pytesseract
import easyocr
from pdf2image import convert_from_bytes
#import comtypes.client
import os
import numpy as np
import cv2

# Specify Tesseract path explicitly
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the TrOCR model and processor for printed text
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed', use_fast=True)
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')

# Initialize EasyOCR reader (default to English, expandable for multi-language)
reader = easyocr.Reader(['en'])  # Add more languages as needed (e.g., ['en', 'hi', 'zh'])

# def convert_doc_to_pdf(doc_path):
#     """Convert DOC/DOCX to PDF on Windows using comtypes."""
#     try:
#         word = comtypes.client.CreateObject('Word.Application')
#         doc = word.Documents.Open(doc_path)
#         pdf_path = doc_path.replace('.doc', '.pdf').replace('.docx', '.pdf')
#         doc.SaveAs(pdf_path, FileFormat=17)  # 17 is PDF format
#         doc.Close()
#         word.Quit()
#         return pdf_path
#     except Exception as e:
#         logger.error(f"DOC to PDF conversion failed: {str(e)}")
#         raise Exception(f"DOC to PDF conversion failed: {str(e)}")

def preprocess_image(image, for_tesseract=False):
    """Preprocess the image adaptively for all text types."""
    try:
        # Preserve aspect ratio with a maximum size
        original_size = image.size
        max_size = 1000 if for_tesseract else 384
        ratio = min(max_size / original_size[0], max_size / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5 if for_tesseract else 1.5)

        # Convert to grayscale
        image = image.convert("L")

        # Adaptive thresholding to handle varying contrast
        image_np = np.array(image)
        if image_np.size > 0:  # Ensure array is not empty
            _, image_binary = cv2.threshold(image_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            image = Image.fromarray(image_binary)

        # Reliable inversion based on histogram
        hist = image.histogram()
        total_pixels = sum(hist)
        dark_pixels = hist[0] + hist[1] + hist[2]  # Sum of dark shades
        if dark_pixels / total_pixels > 0.7:  # If more than 70% pixels are dark
            image = ImageOps.invert(image)

        # Convert back to RGB for TrOCR if needed
        if not for_tesseract:
            image = image.convert("RGB")

        logger.info(f"Image preprocessed: size={image.size}, mode={image.mode}")
        return image
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise Exception(f"Image preprocessing failed: {str(e)}")

def ocr_with_tesseract(image):
    """OCR using Tesseract with optimized settings for all text types."""
    try:
        image = preprocess_image(image, for_tesseract=True)
        # PSM 11 for sparse text with OSD, OEM 1 for LSTM, English as default
        text = pytesseract.image_to_string(image, config='--psm 11 --oem 1 -l eng')
        logger.info(f"Tesseract extracted text: {text[:100]}...")
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
        logger.info(f"TrOCR extracted text: {text[:100]}...")
        return text.strip()
    except Exception as e:
        logger.error(f"TrOCR OCR failed: {str(e)}")
        raise Exception(f"TrOCR OCR failed: {str(e)}")

def ocr_with_easyocr(image, lang='en'):
    """OCR using EasyOCR for multi-language and low-quality images."""
    try:
        image = preprocess_image(image, for_tesseract=True)
        result = reader.readtext(image, detail=0, paragraph=True)  # paragraph=True for better layout
        text = '\n'.join(result)
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

                # Step 1: Try Tesseract (default for printed text)
                tesseract_text = ocr_with_tesseract(image)
                if is_valid_text(tesseract_text):
                    logger.info("Using Tesseract result")
                    results.append(tesseract_text)
                    continue

                # Step 2: Try TrOCR if handwritten or Tesseract fails
                if text_type == "handwritten" or not is_valid_text(tesseract_text):
                    trocr_text = ocr_with_trocr(image)
                    if is_valid_text(trocr_text):
                        logger.info("Using TrOCR result")
                        results.append(trocr_text)
                        continue

                # Step 3: Try EasyOCR for multi-language or low-quality
                easyocr_text = ocr_with_easyocr(image, lang=lang)
                if is_valid_text(easyocr_text):
                    logger.info("Using EasyOCR result")
                    results.append(easyocr_text)
                    continue

                logger.warning("All OCR models failed to produce valid text")
                results.append("Unable to extract text")

            return '\n'.join(results)

        logger.warning("No content to process")
        return "No content to process"

    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise Exception(f"OCR processing failed: {str(e)}")