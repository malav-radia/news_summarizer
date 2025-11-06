# scraper/gnews_scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import feedparser

def get_gnews_headlines():
    """
    Fetches headlines from the official Google News "World" RSS feed.
    This is fast, reliable, and stable.
    """
    print("--- FETCHING WORLD NEWS HEADLINES FROM GOOGLE RSS ---")
    # This is the RSS feed for "World" news
    url = "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-IN&gl=IN&ceid=IN:en"
    
    headlines = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            headlines.append({
                'headline': entry.title,
                'url': entry.link
            })
            
    except Exception as e:
        print(f"An error occurred while parsing Google News RSS feed: {e}")
        return []

    print(f"Found {len(headlines)} World News headlines from RSS. Returning up to 30.")
    return headlines[:30]


def get_gnews_article_text(url):
    """
    Uses our most robust, generic Selenium scraper to fetch article text
    from any link provided by the Google News feed.
    """
    print(f"--- FETCHING GENERIC ARTICLE TEXT WITH SELENIUM FROM: {url} ---")
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

        # Wait for the body tag to be present
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # This is a special step for Google News links: wait for the redirect
        if "google.com" in driver.current_url:
            print("Waiting for Google redirect...")
            WebDriverWait(driver, 60).until(lambda d: "google.com" not in d.current_url)
            print(f"Redirect complete. Final URL: {driver.current_url}")
        
        html_content = driver.page_source
        
    except Exception as e:
        print(f"An error occurred with Selenium while fetching the article: {e}")
        return "This website is actively blocking scraping attempts. Please try another article."
    finally:
        if driver:
            driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # --- Generic Scraper Fallback Logic ---
    
    # Attempt 1: Find an <article> tag
    article_tag = soup.find('article')
    if article_tag:
        print("Found text using <article> tag.")
        paragraphs = article_tag.find_all('p')
        if paragraphs:
            article_text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
            return article_text

    # Attempt 2 (Fallback): Just get all <p> tags on the page
    print("Could not find <article> tag. Falling back to all <p> tags...")
    all_paragraphs = soup.find_all('p')
    if all_paragraphs:
        article_text = '\n\n'.join(p.get_text(strip=True) for p in all_paragraphs)
        if len(article_text) > 300: # Make sure it's real content
            return article_text

    return "Found the page, but could not find the main article content. The layout is unrecognized."