# app.py
from flask import Flask, render_template, jsonify, request
from scraper.toi_scraper import get_toi_headlines, get_toi_article_text
from scraper.gnews_scraper import get_gnews_headlines, get_gnews_article_text
from summarizer.model import summarize_text
from summarizer.categorizer import categorize_text
from datetime import datetime, timedelta
import os
import json # --- NEW: Need this to parse coordinates

# --- Import the OCR processor ---
from ocr.ocr_processor import process_image_ocr

from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class SummaryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    date_saved = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    article_text = db.Column(db.Text, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Summary {self.id} - {self.source}>'

cache = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/history')
def history():
    summaries = SummaryHistory.query.order_by(SummaryHistory.date_saved.desc()).all()
    return render_template('history.html', summaries=summaries)

@app.route('/api/headlines/<publisher>')
def api_headlines(publisher):
    global cache
    
    if publisher in cache and (datetime.now() - cache[publisher].get('timestamp', datetime.min) < timedelta(minutes=10)):
        print(f"--- RETURNING CACHED {publisher.upper()} HEADLINES ---")
        return jsonify(cache[publisher]['headlines'])
    
    print(f"--- FETCHING NEW {publisher.upper()} HEADLINES ---")
    headlines = []
    if publisher == 'toi':
        headlines = get_toi_headlines()
    elif publisher == 'gnews':
        headlines = get_gnews_headlines()
    
    cache[publisher] = {'headlines': headlines, 'timestamp': datetime.now()}
    return jsonify(headlines)

@app.route('/api/get_article', methods=['POST'])
def api_get_article():
    data = request.get_json()
    url = data['url']
    text = "Error: Unknown news source"
    
    if "timesofindia.indiatimes.com" in url:
        text = get_toi_article_text(url)
    else:
        text = get_gnews_article_text(url)
    
    return jsonify({'article_text': text})

@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    data = request.get_json()
    article_text = data['text']
    source = data.get('source', 'Online Article') 
    
    summary = summarize_text(article_text)
    category = categorize_text(summary)
    
    try:
        new_entry = SummaryHistory(
            source=source,
            article_text=article_text,
            summary_text=summary,
            category=category
        )
        db.session.add(new_entry)
        db.session.commit()
        print(f"--- Saved '{source}' summary to database. ---")
    except Exception as e:
        print(f"Error saving to database: {e}")
        db.session.rollback()
    
    return jsonify({'summary': summary, 'category': category})

# --- NEW: HUMAN-IN-THE-LOOP OCR ENDPOINT ---
@app.route('/api/ocr-summarize-manual', methods=['POST'])
def api_ocr_summarize_manual():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400
    
    file = request.files['image']
    gaps_json = request.form.get('gaps')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
        
    try:
        # Get the gap coordinates from the user
        gaps = json.loads(gaps_json)
        print(f"--- RUNNING MANUAL OCR with gaps at: {gaps} ---")
        
        # 1. Get the text, passing the user-defined gaps
        extracted_text = process_image_ocr(file, gaps)
        
        if "Could not" in extracted_text or "Error" in extracted_text:
             return jsonify({'error': extracted_text}), 400
        
        # 2. Summarize the extracted text
        print("--- SUMMARIZING OCR TEXT ---")
        summary = summarize_text(extracted_text)
        
        # 3. Categorize the summary
        print("--- CATEGORIZING OCR TEXT ---")
        category = categorize_text(summary)
        
        # 4. Save to database
        try:
            new_entry = SummaryHistory(
                source="OCR Upload (Manual)", # New source
                article_text=extracted_text,
                summary_text=summary,
                category=category
            )
            db.session.add(new_entry)
            db.session.commit()
            print("--- Saved 'OCR Upload (Manual)' summary to database. ---")
        except Exception as e:
            print(f"Error saving to database: {e}")
            db.session.rollback()

        return jsonify({
            'extracted_text': extracted_text,
            'summary': summary,
            'category': category
        })
        
    except Exception as e:
        print(f"An error occurred in api_ocr_summarize_manual: {e}")
        return jsonify({'error': f'An internal server error occurred: {e}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)