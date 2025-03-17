from flask import Blueprint, request, jsonify
from .ocr import ocr_process
from .translate import translate_text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/process', methods=['POST'])
def process():
    try:
        logger.info("Received process request")
        # Get form data
        form_data = request.form
        text = form_data.get('text', '')
        file = request.files.get('file')
        option = form_data.get('option', 'ocr')
        source_lang = form_data.get('source_lang', 'auto')
        target_lang = form_data.get('target_lang', 'en')

        logger.info(f"Options - Text: {text[:50]}, File: {file.filename if file else None}, Option: {option}, Source: {source_lang}, Target: {target_lang}")

        # Validate inputs
        if not text and not file:
            logger.warning("No text or file provided")
            return jsonify({'error': 'Please provide either text or a file'}), 400

        # Process based on the option
        if option == 'ocr':
            # Use source_lang for EasyOCR if needed
            lang = target_lang if target_lang != 'en' else 'en'
            result = ocr_process(text, file, lang=lang)
        elif option == 'translate':
            result = translate_text(text, file, source_lang, target_lang)
        else:
            logger.error("Invalid option provided")
            return jsonify({'error': 'Invalid option'}), 400

        logger.info(f"Processing successful, result length: {len(result)}")
        return jsonify({'result': result})

    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        return jsonify({'error': str(e)}), 500