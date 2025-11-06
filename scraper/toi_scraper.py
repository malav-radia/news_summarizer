# scraper/toi_scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
# --- NEW: Import feedparser ---
import feedparser 

def get_toi_headlines():
    """
    Fetches headlines from the official Times of India RSS feed.
    This is fast, reliable, and stable.
    """
    print("--- FETCHING TOI HEADLINES FROM RSS FEED ---")
    # This is the official RSS feed for TOI Top Stories
    url = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
    
    headlines = []
    try:
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            headlines.append({
                'headline': entry.title,
                'url': entry.link
            })
            
    except Exception as e:
        print(f"An error occurred while parsing TOI RSS feed: {e}")
        return []

    print(f"Found {len(headlines)} TOI headlines from RSS. Returning up to 30.")
    return headlines[:30]


def get_toi_article_text(url):
    """
    Uses a robust Selenium instance to fetch the full article text from TOI.
    """
    print(f"--- FETCHING TOI ARTICLE TEXT WITH SELENIUM FROM: {url} ---")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(60)

        try:
            driver.get(url)
        except TimeoutException:
            print("Page load for article timed out.")
            driver.quit()
            return "Could not load the article page in time. It may be blocking requests."

        # Wait for the main article div (class _s30J)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "_s30J")))
        
        html_content = driver.page_source
        
    except Exception as e:
        print(f"An error occurred with Selenium while fetching the article: {e}")
        return "This website is actively blocking scraping attempts. Please try another article."
    finally:
        if driver:
            driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    article_div = soup.find('div', class_='_s30J')
    
    if article_div:
        return article_div.get_text(separator='\n\n', strip=True)
    else:
        return "Found the page, but could not find the main article content. The layout may have changed."