from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the M2M-100 model and tokenizer
model_name = "facebook/m2m100_418M"
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
model = M2M100ForConditionalGeneration.from_pretrained(model_name)

def translate_text(text, file, source_lang, target_lang):
    try:
        # If a file is provided, extract text using OCR
        if file:
            from .ocr import ocr_process
            text = ocr_process("", file, lang=source_lang if source_lang != 'auto' else 'en')
            logger.info(f"OCR extracted text: {text[:100]}...")

        if not text:
            logger.warning("No text to translate")
            return "No text to translate"

        # Map language codes to M2M-100 format
        lang_map = {
            'auto': None,
            'en': 'en',
            'hi': 'hi',
            'fr': 'fr',
            'es': 'es'
        }
        src_lang_code = lang_map.get(source_lang, 'en')
        tgt_lang_code = lang_map.get(target_lang, 'en')

        # Detect source language if 'auto' is specified
        if src_lang_code is None:
            # Check for Devanagari script (Hindi)
            if any(ord(c) in range(2304, 2432) for c in text):  # Devanagari Unicode range
                src_lang_code = 'hi'
                logger.info("Detected source language: Hindi")
            else:
                # Fallback: default to English if no clear detection
                src_lang_code = 'en'
                logger.info("Defaulting source language to English")

        # Ensure translation occurs even if source and target languages are the same
        if src_lang_code == tgt_lang_code:
            logger.info(f"Source ({src_lang_code}) and target ({tgt_lang_code}) languages are the same; returning original text")
            return text

        # Set source language
        tokenizer.src_lang = src_lang_code

        # Tokenize and translate
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        translated_ids = model.generate(**inputs, forced_bos_token_id=tokenizer.get_lang_id(tgt_lang_code))
        translated_text = tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]

        logger.info(f"Translated from {src_lang_code} to {tgt_lang_code}: {translated_text}")
        return translated_text

    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise Exception(f"Translation failed: {str(e)}")