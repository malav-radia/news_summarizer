import pandas as pd
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Define the paths to your dataset
DATA_DIR = "BBC News Summary"
ARTICLES_DIR = os.path.join(DATA_DIR, "News Articles")
SUMMARIES_DIR = os.path.join(DATA_DIR, "Summaries")
CATEGORIES = ["business", "entertainment", "politics", "sport", "tech"]

def clean_text(text):
    """
    A simple function to clean the text:
    - Remove extra newlines
    - Remove datelines or author lines (e.g., "By...")
    - Strip leading/trailing whitespace
    """
    # Remove extra newlines and tabs
    text = re.sub(r'\s+', ' ', text).strip()
    # You could add more complex cleaning here if needed
    return text

def load_data():
    """
    Loads articles and summaries from the folders into a pandas DataFrame.
    """
    data = []
    
    print("Loading data from folders...")
    
    for category in CATEGORIES:
        article_path = os.path.join(ARTICLES_DIR, category)
        summary_path = os.path.join(SUMMARIES_DIR, category)
        
        # Get all file names
        files = os.listdir(article_path)
        
        for file_name in files:
            # Read the article
            with open(os.path.join(article_path, file_name), 'r', encoding='utf-8', errors='ignore') as f:
                article = f.read()
                
            # Read the summary
            with open(os.path.join(summary_path, file_name), 'r', encoding='utf-8', errors='ignore') as f:
                summary = f.read()
                
            data.append({
                'category': category,
                'article': clean_text(article),
                'summary': clean_text(summary)
            })
            
    print(f"Loaded {len(data)} article/summary pairs.")
    return pd.DataFrame(data)

def perform_eda(df):
    """
    Performs and displays Exploratory Data Analysis (EDA).
    """
    print("\n--- EDA: Data Analysis ---")
    
    # 1. Check for null values
    print("Checking for null values:")
    print(df.isnull().sum())

    # 2. Analyze text lengths
    df['article_length'] = df['article'].apply(lambda x: len(x.split()))
    df['summary_length'] = df['summary'].apply(lambda x: len(x.split()))
    
    print("\nText Length Statistics (in words):")
    print(df[['article_length', 'summary_length']].describe())
    
    # 3. Plot histograms of text lengths
    print("Generating length distribution plots...")
    
    plt.figure(figsize=(12, 6))
    
    # Article length histogram
    plt.subplot(1, 2, 1)
    sns.histplot(df['article_length'], bins=50, kde=True)
    plt.title('Article Length Distribution')
    plt.xlabel('Number of Words')
    plt.ylabel('Frequency')
    
    # Summary length histogram
    plt.subplot(1, 2, 2)
    sns.histplot(df['summary_length'], bins=30, kde=True)
    plt.title('Summary Length Distribution')
    plt.xlabel('Number of Words')
    
    plt.suptitle('EDA: Text Length Analysis')
    plt.savefig('length_analysis.png')
    print("Saved length analysis plot to 'length_analysis.png'")

# --- Main execution ---
if __name__ == "__main__":
    # 1. Load and clean data
    dataframe = load_data()
    
    # 2. Perform EDA
    perform_eda(dataframe)
    
    # 3. Save the clean data to a single CSV file
    # We drop the length columns as they were just for analysis
    clean_df = dataframe[['article', 'summary', 'category']]
    clean_df.to_csv('bbc_news_cleaned.csv', index=False)
    
    print("\n--- Preprocessing Complete ---")
    print("Cleaned data saved to 'bbc_news_cleaned.csv'")