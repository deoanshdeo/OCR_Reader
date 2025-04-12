# This file helps translate text from one language to another.
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from langdetect import detect
import logging
import os

# Ensure dependencies are installed
required_packages = ['torch', 'transformers', 'langdetect', 'unidecode', 'indic-transliteration']

# Checks for all the tools we need and installs them if they're missing.
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        os.system(f"pip install {package}")

from unidecode import unidecode
from indic_transliteration import sanscript

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load M2M-100 model and tokenizer
model_name = "facebook/m2m100_418M"
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
model = M2M100ForConditionalGeneration.from_pretrained(model_name)

# Force CPU usage (avoid CUDA issues)
DEVICE = "cpu"
model.to(DEVICE)
logger.info(f"Using device: {DEVICE}")

# Supported languages (matches your Form.js options)
LANG_MAP = {
    'en': 'en',  # English
    'hi': 'hi',  # Hindi
    'fr': 'fr',  # French
    'es': 'es',  # Spanish
    'ru': 'ru',  # Russian
    'ta': 'ta',  # Tamil
}

def transliterate_text(text, source_lang):
    """Transliterate text to Roman (ASCII) using unidecode."""
    try:
        transliterated = unidecode(text)
        if transliterated == text:
            logger.info(f"No transliteration needed or possible for {source_lang}: {text[:50]}...")
        else:
            logger.info(f"Transliterated {source_lang} to Roman: {transliterated[:50]}...")
        return transliterated
    except Exception as e:
        logger.error(f"Transliteration failed: {str(e)}")
        return text

# Converts Hindi written in English letters (like "mujhe", etc.)
def roman_to_devanagari(text):
    """Convert Romanized Hindi to Devanagari script with normalization."""
    try:
        # Normalize common casual Romanization for ITRANS compatibility
        text = text.lower()  # ITRANS is case-insensitive, but let’s standardize
        text = text.replace("ki", "kii")  # Adjust short "ki" to long "kii"
        text = text.replace("chahiye", "chaahiye")  # Fix common ending
        text = text.replace("jana", "jaanaa")  # Lengthen vowels
        text = text.replace("laga", "lagaa")  # Lengthen vowels
        text = text.replace("mujhe", "mujhe")  # Already correct, but explicit

        # Convert to Devanagari using ITRANS
        devanagari_text = sanscript.transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
        logger.info(f"Converted Roman to Devanagari: {devanagari_text[:50]}...")
        return devanagari_text
    except Exception as e:
        logger.error(f"Roman to Devanagari conversion failed: {str(e)}")
        return text

def translate_text(text, file, source_lang, target_lang):
    """Translate text from source_lang to target_lang, handling Romanized Hindi."""
    try:
        # If a file is provided, extract text using OCR
        if file:
            from .ocr import ocr_process
            text = ocr_process("", file, lang=source_lang if source_lang != 'auto' else 'en')
            logger.info(f"OCR extracted text: {text[:100]}...")

        if not text:
            logger.warning("No text to translate")
            return "No text to translate"

        # Map language codes
        src_lang = LANG_MAP.get(source_lang, 'en')
        tgt_lang = LANG_MAP.get(target_lang, 'en')

        # Auto-detect source language if 'auto'
        if source_lang == 'auto':
            src_lang = detect(text)
            if src_lang not in LANG_MAP:
                src_lang = 'en'
            logger.info(f"Detected source language: {src_lang}")

        # Preprocess Romanized Hindi to Devanagari if source is Hindi and text is Roman
        if src_lang == 'hi' and not any(ord(c) >= 2304 and ord(c) <= 2431 for c in text):
            text = roman_to_devanagari(text)

        # Transliterate (for logging/debugging, not returned)
        transliterated = transliterate_text(text, src_lang)

        # Skip translation if source and target are the same
        if src_lang == tgt_lang:
            logger.info(f"Source ({src_lang}) and target ({tgt_lang}) are the same")
            return text

        # Translate
        tokenizer.src_lang = src_lang
        inputs = tokenizer(text, return_tensors="pt", padding=True).to(DEVICE)
        translated_ids = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.get_lang_id(tgt_lang),
            max_length=256,
            num_beams=5
        )
        translated = tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]
        logger.info(f"Translated from {src_lang} to {tgt_lang}: {translated}")
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise Exception(f"Translation failed: {str(e)}")