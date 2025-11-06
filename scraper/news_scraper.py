# scraper/news_scraper.py
import feedparser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait

def get_headlines(category='general'):
    """
    Fetches headlines from a specific Google News RSS feed based on the category.
    """
    print(f"Fetching headlines for category: {category}")
    
    # Map our category names to the specific Google News RSS URLs
    category_urls = {
        'general': 'https://news.google.com/rss?ned=in&hl=en-IN&gl=IN',
        'business': 'https://news.google.com/rss/headlines/section/topic/BUSINESS.en_in/BUSINESS?ned=in&hl=en-IN&gl=IN',
        'technology': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY.en_in/TECHNOLOGY?ned=in&hl=en-IN&gl=IN',
        'sports': 'https://news.google.com/rss/headlines/section/topic/SPORTS.en_in/SPORTS?ned=in&hl=en-IN&gl=IN',
        'entertainment': 'https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT.en_in/ENTERTAINMENT?ned=in&hl=en-IN&gl=IN'
    }
    
    # Get the correct URL, or fall back to the general one
    url = category_urls.get(category, category_urls['general'])
    
    headlines = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            headlines.append({
                'headline': entry.title,
                'url': entry.link
            })
    except Exception as e:
        print(f"An error occurred while parsing RSS feed: {e}")
        return []

    print(f"Found {len(headlines)} headlines from RSS. Returning up to 30.")
    return headlines[:30]

def get_article_text(url):
    # This function remains unchanged
    print(f"Fetching article with Selenium from: {url}")
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
        driver.get(url)

        print("Waiting for redirect...")
        WebDriverWait(driver, 60).until(lambda d: "google.com" not in d.current_url)
        print(f"Redirect complete. Final URL: {driver.current_url}")
        
        html_content = driver.page_source
        
    except Exception as e:
        print(f"An error occurred with Selenium: {e}")
        return "This website is actively blocking scraping attempts or timed out after 60 seconds. Please try another article."
    finally:
        if driver:
            driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    possible_selectors = ['article', 'div.article-body', 'div.story-body', 'div.main-content']
    
    article_body = None
    for selector in possible_selectors:
        article_body = soup.select_one(selector)
        if article_body:
            print(f"Extracting text using selector: {selector}")
            break
    
    if article_body:
        for tag in article_body(['script', 'style']):
            tag.decompose()
        return article_body.get_text(separator='\n\n', strip=True)
    else:
        return "Found the page, but could not automatically find the main article content."