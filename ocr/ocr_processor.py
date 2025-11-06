# ocr/ocr_processor.py

import pytesseract
from PIL import Image
import os
import cv2
import numpy as np
import pandas as pd # Keep pandas, it's a dependency for the main app

# --- TESSERACT PATH ---
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    print("Tesseract not found at C:\\Program Files\\Tesseract-OCR\\. Hoping it's in the system PATH.")

def process_image_ocr(image_file, gaps):
    """
    Performs robust OCR by:
    1. Using the human-provided 'gaps' (a list of x-coordinates) to crop.
    2. Running the simple 'image_to_string' with PSM 6 on each column.
    """
    try:
        pil_image = Image.open(image_file).convert('L') # Convert to grayscale
        
        # --- 1. Create column boundaries from the user's gaps ---
        boundaries = [0] + gaps + [pil_image.width]
        
        all_text_columns = []

        # --- 2. Crop Image and Run Tesseract on each Column ---
        for i in range(len(boundaries) - 1):
            left = boundaries[i]
            right = boundaries[i+1]
            
            # Add a 5px buffer to avoid cutting text
            left_buffered = max(0, left - 5)
            right_buffered = min(pil_image.width, right + 5)
            
            # Check if the crop is valid
            if (right_buffered - left_buffered) < 20: # If crop is less than 20px wide
                continue

            column_crop_pil = pil_image.crop((left_buffered, 0, right_buffered, pil_image.height))
            
            print(f"--- Processing User Column {i+1} (Pixels {left_buffered} to {right_buffered}) ---")
            
            # --- 3. THIS IS THE NEW, SIMPLE LOGIC ---
            # Stop using image_to_data.
            # Use image_to_string with PSM 6: "Assume a single uniform block of text."
            col_text = pytesseract.image_to_string(
                column_crop_pil, 
                config='--psm 6'
            )
            
            all_text_columns.append(" ".join(col_text.split())) # Clean up whitespace

        # --- 4. Join the text ---
        final_text = "\n\n".join(all_text_columns) # Join the 3 long strings
        
        if not final_text:
            return "Could not extract any text. Try a clearer image."
            
        return final_text

    except pytesseract.TesseractNotFoundError:
        print("\n--- TESSERACT NOT FOUND ---")
        return "Error: Tesseract-OCR engine not found. Check server logs."
    except Exception as e:
        print(f"Error in OCR processing: {e}")
        return f"Error: Could not process the image. {e}"