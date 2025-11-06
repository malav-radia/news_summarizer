# summarizer/categorizer.py
from transformers import pipeline

print("Loading text classification model...")
# Using the smaller, faster, distilled model
classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-3")
print("Text classification model loaded.")

def categorize_text(text):
    """
    Categorizes a given text using a fast, zero-shot classification model.
    """
    # We will categorize the summary, so the text will already be short
    candidate_labels = ['Business', 'Technology', 'Sports', 'Entertainment', 'Politics', 'Science', 'World News']
    
    try:
        result = classifier(text, candidate_labels)
        
        top_category = result['labels'][0]
        print(f"Article categorized as: {top_category}")
        return top_category

    except Exception as e:
        print(f"An error occurred during categorization: {e}")
        return "Uncategorized"