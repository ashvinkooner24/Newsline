import requests
import time
import os
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Create folder to store articles
os.makedirs("rag-source-testing", exist_ok=True)

SITEMAP_URL = "https://www.als.org/sitemap.xml"

# patterns
KEEP_PATTERNS = ["/understanding-als/", "/navigating-als/", "/research/"]  # only keep URLs containing these
SKIP_PATTERNS = []  # skip URLs containing these

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

print("Downloading sitemap...")
driver.get(SITEMAP_URL)

input("If verification appears, solve it then press Enter...")
html = driver.page_source
soup = BeautifulSoup(html, "xml")

urls = [loc.text for loc in soup.find_all("loc")]

print(f"Found {len(urls)} articles")

filtered_urls = []
for url in urls:
    if any(keep in url for keep in KEEP_PATTERNS) and not any(skip in url for skip in SKIP_PATTERNS):
        filtered_urls.append(url)
print(f"Filtered down to {len(filtered_urls)} articles")

for i, url in enumerate(filtered_urls[:5]):  # only first 5 for testing
    print(f"Crawling {url}")

    try:
        article = Article(url)
        article.download()
        article.parse()

        safe_title = article.title.replace(" ", "_").replace("/", "")
        filename = f"rag-source/{safe_title}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(article.text)

        print(f"Saved {filename}")

    except Exception as e:
        print("Error:", e)

    time.sleep(1)

print("Done.")
