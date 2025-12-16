# ocr/ocr_processor.py (The CORRECT version)

import pytesseract
from PIL import Image
import os
import cv2
import numpy as np
import pandas as pd

# --- TESSERACT PATH ---
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    print("Tesseract not found. Hoping it's in the system PATH.")

def process_image_ocr(image_file, gaps): # gaps will be unused
    try:
        pil_image = Image.open(image_file).convert('L')

        # This is the "broken" part - just running tesseract on the whole image
        print("--- RUNNING FAILED AUTO-OCR (FOR SCREENSHOT) ---")
        text = pytesseract.image_to_string(pil_image) 

        return text
    except Exception as e:
        return f"Error: {e}"