# OCR Reader & Translator
 
Welcome to the OCR Reader & Translator, an innovative full-stack application designed to extract text from images and PDFs using Optical Character Recognition (OCR), detect code snippets, and translate content across multiple languages. This project combines a sleek React-based frontend with a robust Flask-powered backend, offering a seamless user experience for processing and translating text.

## Overview

This project is a powerful tool for digitizing documents and translating terms effortlessly. The frontend provides an intuitive interface with features like text input, file uploads, image pasting, and theme switching, while the backend handles advanced OCR and translation using state-of-art models like `TrOCR` and `M2M100`. This project is a subcomponent of another project, available at https://github/deoanshdeo/Project-starts.

- ### Tech Stack
  - Frotend: React, Tailwind CSS, Axios, React Icons, React Transition Group
  - Backend: Python, Flask, Transformers, EasyOCR, pytesseract, OpenCV

- ### Key Features:
  - Multi-engine OCR (Tesseract, EasyOCR, TrOCR)
  - Code detection and extraction from Image
  - Multilingual translation (Englisj, Hindi, French, Spanish, etc.)
  - Drag-and-drop and paste image support

- ### Status:
  - The project is developed. Now I am working on improving it.

## Project Structure

The project is organized as follows:

- ### OCR_Reader/
    - #### backend/
        - **app**/
            - `__init__.py` (Flask application factory)
            - `ocr.py` (OCR processing logic)
            - `routes.py` (API route definitions)
            - `translate.py` (Translation logic)
            - `main.py` (Entry point)
        - `README.md` (Backend documentation)
        - `requirements.txt` (Backend dependencies)
    - #### frontend/
        - ##### public/
            - `index.html` (Main HTML file)
            - `manifest.json` (PWA configuration)
        - ##### src/
            - **components**/
                - `Form.js` (Main form component)
                - `Popup.js` (Result popup component)
                - `ThemeSwitch.js` (Theme toggle component)
            - `App.js` (Main app component)
            - `App.test.js` (Test file)
            - `index.css` (Custom CSS)
            - `index.js` (Entry point)
        - `package.json` (Frontend dependencies)
        - `tailwind.config.js` (Tailwind CSS configuration)
    - **README.md** (This file!)

## Getting Started

Follow these steps to set up and run the project locally.

- ### Prerequisites:
  - Node.js and npm (for frontend)
  - Python 3.9+ (Setting up Anaconda environment will be a much more viable option.)
  - Tesseract OCR installed.
    -  Set path in `backend/app/ocr.py`
    - E.g., `pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'`
  
- ### Installation:
1. Clone the Repository
- ```
  https://github.com/deoanshdeo/OCR_Reader.git
2. Download and install the Tesseract OCR for the image-extraction feature
- You can make use of the following steps for this:
- Update package lists:
    ```
  sudo apt update
- Install Tesseract OCR core:
    ```
    sudo apt install tesseract-ocr
  ```
  This installs the main Tesseract OCR engine, which provides the core functionality for optical character recognition.
-  Install language data packages.
    ```
   sudo apt install tesseract-ocr-eng
   sudo apt install tesseract-ocr-hin
   ```
   These commands install specific language data for Tesseract:
    - tesseract-ocr-eng: English language support
    - tesseract-ocr-hin: Hindi language support
   You can install these simultaneously with:
      ```
      sudo apt install tesseract-ocr-eng tesseract-ocr-hin
      ```
  



























