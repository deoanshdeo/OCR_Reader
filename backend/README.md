# OCR Reader Backend

Welcome to the **OCR Reader Backend**, a powerful Flask-based application designed to handle Optical Character Recognition (OCR) and text translation. This backend serves as the core processing engine for extracting text from images and PDFs, detecting code, and translating content across multiple languages using cutting-edge machine learning models.

## Overview
Built with Python and Flask, the OCR Reader Backend integrates advanced libraries like `pytesseract`, `EasyOCR`, and `Transformers` (TrOCR and [M2M100](https://huggingface.co/facebook/m2m100_418M)) to deliver high-accuracy text extraction and translation. It is modular, extensible, and optimized for tasks such as document digitization, multilingual support, and code recognition from visual inputs.

* **Tech Stack**: Python, Flask, OpenCV, Transformers, EasyOCR, pytesseract
* **Key Features**: Multi-engine OCR, code detection, multilingual translation, robust error handling
* **Status**: Actively developed as of April 10, 2025

## Project Structure for Backend

The backend directory is organized as follows:

```
OCR_Reader/backend/
├── app/
│   ├── __init__.py       # Flask application factory
│   ├── ocr.py            # OCR processing logic (Tesseract, EasyOCR, TrOCR)
│   ├── routes.py         # API route definitions
│   ├── translate.py      # Text translation using M2M100 model
│   └── main.py           # Entry point to run the Flask app
├── README.md             # This file!
└── requirements.txt      # Python dependencies
```

- **app/**: Contains the core application logic.
    - **__init__.py**: Sets up the Flask app with CORS support.
    - **ocr.py**: Implements OCR pipelines with preprocessing and post-processing for text and code.
    - **routes.py**: Defines the `/process` API endpoint for OCR and translation.
    - **translate.py**: Handles text translation with language detection and transliteration.
    - **main.py**: Launches the Flask server.
- **requirements.txt**: Lists all required Python packages.
- **README.md**: Documentation for the backend.

## Getting Started

Follow these steps to set up and run the backend locally.

### Prerequisites

- Python 3.8+
- Tesseract OCR installed (set path in ocr.py if needed, e.g., `pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'`)

Installation

1. Navigate to the Backend Directory
   ```
    cd OCR_Reader/backend
   ```

2. Install Dependencies Install the required Python packages:
    ```
    pip install -r requirements.txt
    ```
3. Run the Application Start the Flask server:
    ```
    python main.py
    ```
    The backend will be accessible at `http://0.0.0.0:500`

## API Endpoints

- POST `/process`
 - Description: Process text or files (image/PDFs) for OCR or translation.
 - Parameters:
   * `text` (string, optional): Input text to process.
   * `file` (file, optional): Uploaded image or PDF file.
   * `option` (string, default: `ocr`): Choose `ocr` or `translate`.
   * `source_lang` (string, default: `auto`):Source language (e.g., `en`, `hi`, `fr`).
   * `target_lang` (string, default: `en`): Target language (e.g., `en`, `hi`, `fr`).

- Response: JSON object with `result` or `error` key.

## Features

- **Multi-Engine OCR**: Utilizes Tesseract, EasyOCR, and TrOCR for versatile text extraction.
- **Code Detection**: Optimized preprocessing and post-processing for recognizing code snippets.
- **Multilingual** Support: Supports languages like English, French, German, Hindi, and more.
- **Translation**: Powered by the M2M100 model for accurate multilingual translation.
- **Error Handling**: Includes logging and fallback mechanisms for reliability.

## Contact

* Author: Deoansh Deo
* Email: [deoanshdeo@gmail.com](mailto:deoanshdeo@gmail.com) [![Email](https://img.shields.io/badge/-Email-red?style=flat&logo=gmail&logoColor=white)](mailto:deoanshdeo@gmail.com)
* GitHub: [github.com/deoanshdeo](https://github.com/deoanshdeo) [![GitHub](https://img.shields.io/badge/-GitHub-black?style=flat&logo=github&logoColor=white)](https://github.com/deoanshdeo)
* LinkedIn: [linkedin.com/in/deoansh-deo-b0456922a](https://www.linkedin.com/in/deoansh-deo-b0456922a) [![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/deoansh-deo-b0456922a)




















