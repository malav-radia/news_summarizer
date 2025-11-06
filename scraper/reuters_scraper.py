# scraper/reuters_scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import feedparser

def get_reuters_headlines():
    """
    Fetches headlines from the official Reuters Top News RSS feed.
    This is fast, reliable, and stable.
    """
    print("--- FETCHING REUTERS HEADLINES FROM RSS FEED ---")
    
    # --- UPDATED URL ---
    # Switched from the old "worldNews" feed to the more reliable "topNews" feed
    url = "https://www.reuters.com/rss/topNews"
    
    headlines = []
    try:
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            headlines.append({
                'headline': entry.title,
                'url': entry.link
            })
            
    except Exception as e:
        print(f"An error occurred while parsing Reuters RSS feed: {e}")
        return []

    print(f"Found {len(headlines)} Reuters headlines from RSS. Returning up to 30.")
    return headlines[:30]


def get_reuters_article_text(url):
    """
    Uses Selenium to fetch the full article text from a Reuters page.
    """
    print(f"--- FETCHING REUTERS ARTICLE TEXT WITH SELENIUM FROM: {url} ---")
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
        
        html_content = driver.page_source
        
    except Exception as e:
        print(f"An error occurred with Selenium while fetching the article: {e}")
        return "This website is actively blocking scraping attempts. Please try another article."
    finally:
        if driver:
            driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Attempt 1: Find all paragraphs with the specific testid
    paragraphs = soup.find_all('p', attrs={"data-testid": "Paragraph"})
    if paragraphs:
        print("Found text using data-testid selector.")
        article_text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
        return article_text

    # Attempt 2 (Fallback): Find the <article> tag and get all <p> tags inside it
    print("Could not find data-testid. Falling back to <article> tag...")
    article_tag = soup.find('article')
    if article_tag:
        paragraphs = article_tag.find_all('p')
        if paragraphs:
            print("Found text using <article> fallback.")
            article_text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
            return article_text

    # Attempt 3 (Final Fallback): Just get all <p> tags on the page
    print("Could not find <article> tag. Falling back to all <p> tags...")
    all_paragraphs = soup.find_all('p')
    if all_paragraphs:
        article_text = '\n\n'.join(p.get_text(strip=True) for p in all_paragraphs)
        return article_text

    return "Found the page, but could not find the main article content. The layout is unrecognized."