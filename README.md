# 📰 QuickRead News Summarizer

QuickRead is a Flask-based web application designed to fetch and summarize news articles efficiently. 
It offers two main features — summarizing live articles scraped from the web and summarizing text from uploaded newspaper images using a robust human-in-the-loop OCR interface.

---

## ✨ Key Features

### 🗞️ Online Article Summarizer
- Fetches top headlines from sources like Times of India and Google News.
- Scrapes the full text of any selected article.
- Uses a fine-tuned BART model (via Hugging Face) to generate high-quality abstractive summaries.
- Categorizes summaries into topics such as Politics, Technology, Sports, etc.

### 📰 Newspaper OCR Summarizer (Human-in-the-Loop)
- Allows users to upload newspaper images (JPG, PNG).
- Provides an interactive click-to-mark UI to identify column gaps manually.
- This human-in-the-loop design fixes common OCR failures on multi-column layouts.
- Uses the provided coordinates to crop the image accurately before running Tesseract OCR on each column.
- Ensures a proper reading order and higher accuracy in text extraction.

### 🧾 Summary History
- All generated summaries (both online and OCR) are stored in a local SQLite database.
- A “History” page lets you view and revisit all your past summaries.

---

## 🛠️ Technologies Used

Backend: Flask, Flask-SQLAlchemy  
Scraping: Requests, BeautifulSoup4 (bs4)  
NLP / Summarization: Hugging Face transformers, PyTorch  
OCR & Image Processing: Pytesseract, OpenCV, SciPy  
Frontend: HTML, CSS, JavaScript  
Database: SQLite  

---

## 🚀 How to Run This Project

Follow these steps to set up and run QuickRead locally.

### Step 1: Clone the Repository
git clone https://github.com/malav-radia/news_summarizer.git  
cd news_summarizer  

---

### Step 2: Create a .gitignore File

This prevents uploading unnecessary files like your virtual environment and database to GitHub.  
Create a `.gitignore` file in your project root and paste this:

# Virtual Environment
venv/
__pycache__/

# Local Database
database.db

# IDE settings
.vscode/

---

### Step 3: Create a Virtual Environment

Windows:
python -m venv venv  
venv\Scripts\activate  

macOS/Linux:
python3 -m venv venv  
source venv/bin/activate  

---

### Step 4: Install Tesseract OCR (External Dependency)

This project requires the Tesseract OCR engine.  
Download the 64-bit installer from: https://digi.bib.uni-mannheim.de/tesseract/  
During installation, check the box that says “Add Tesseract to system PATH.”  
Restart your terminal or code editor after installation.

---

### Step 5: Install Python Requirements
pip install -r requirements.txt  

---

### Step 6: Run the Application
python app.py  

The application will be running at:  
http://127.0.0.1:5000  

---

## 🧠 Future Enhancements
- Integration of multilingual summarization.
- Improved UI for faster human-in-the-loop marking.
- Support for PDF uploads and scanned archives.

---

## 🪪 License
This project is open-source and available under the MIT License.

---

Developed with ❤️ using Flask, Hugging Face, and a pinch of AI.
