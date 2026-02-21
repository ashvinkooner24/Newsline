import requests
import time
import os
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urljoin, urlparse
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Create folder to store articles
FOLDER_NAME = "rag-source/final"
MAX_PAGES_PER_SITE = 1000  
os.makedirs(FOLDER_NAME, exist_ok=True)

def fetch_sitemap_urls(sitemap_url, site_metadata):

    """
    Recursively fetch all URLs from a sitemap or sitemap index.
    """
    urls = []
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")

        # If sitemap index, recurse
        sitemap_index = soup.find("sitemapindex")
        if sitemap_index:
            for sitemap in sitemap_index.find_all("loc"):
                urls += fetch_sitemap_urls(sitemap.text, site_metadata)
        else:
            # urlset
            for loc in soup.find_all("loc"):
                site_metadata["total_pages_found"] += 1
                urls.append(loc.text)
    except Exception as e:
        site_metadata["total_pages_failed"] += 1
        print(f"Failed to fetch sitemap {sitemap_url}: {e}")
    return urls

def fetch_recursive_urls(start_url, safe_folder, use_selenium = False, extraction_method = "article", extraction_config = [], keep_keywords = [], skip_keywords = [], site_metadata = {}):

    """
    Recursively fetch URLs starting from start_url, staying within base_domain.
    """
    visited = set()
    to_visit = [start_url]
    urls = []

    while to_visit:
        if site_metadata["total_pages_saved"] >= MAX_PAGES_PER_SITE:
            print("Reached page limit, stopping crawl.")
            break
        url = to_visit.pop()

        if url in visited:
            continue

        print("Visiting:", url)
        visited.add(url)
        urls.append(url)
        site_metadata["total_pages_found"] += 1
        
        crawl_and_save([url], 1, safe_folder, extraction_method, extraction_config, keep_keywords, skip_keywords, site_metadata)  # crawl and save as we go to avoid losing data if crawl is interrupted

        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print("Failed:", url)
                site_metadata["total_pages_failed"] += 1
        except Exception as e:
            print("Error:", url)
            site_metadata["total_pages_failed"] += 1
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        find_link = 0
        for link in soup.find_all("a", href=True):
            href = link["href"]

            full_url = urljoin(url, href)
            full_url = full_url.split("#")[0]  # remove fragment

            parsed = urlparse(full_url)

            if full_url in visited:
                continue

            if parsed.netloc != urlparse(url).netloc:
                continue

            if not full_url.startswith(start_url):
                site_metadata["total_pages_skipped"] += 1
                continue

            find_link+=1
            to_visit.append(full_url)

        if use_selenium and find_link <= 1:  # heuristic: if we found very few links, maybe it's a JS-heavy page where links are generated dynamically and not present in the initial HTML
            print(f"No new links found on {url} using standard method.")
            to_visit.extend(fetch_selenium_urls(start_url, url, visited, site_metadata))  # try Selenium as fallback for JS-heavy pages

    return urls

def fetch_selenium_urls(start_url, page_url, visited, site_metadata = {}):
    """
    Fetch URLs from a page that relies on JavaScript for navigation using Selenium.
    """
    print(f"Fetching URLs from {page_url} using Selenium...")

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(page_url)

    # Find all <script> tags
    scripts = driver.find_elements("tag name", "script")

    urls = []
    for s in scripts:
        js = s.get_attribute("innerHTML")
        matches = re.findall(r'location\.href\s*=\s*"([^"]+)"', js)
        
        for match in matches:
            full_url = urljoin(page_url, match)
            full_url = full_url.split("#")[0]  # remove fragment

            parsed = urlparse(full_url)

            if full_url in visited:
                continue

            if parsed.netloc != urlparse(page_url).netloc:
                site_metadata["total_pages_skipped"] += 1
                continue

            if not full_url.startswith(start_url):
               site_metadata["total_pages_skipped"] += 1
               continue

            if full_url not in visited:
                urls.append(full_url)

    driver.quit()
    print(f"Found {len(urls)} URLs using Selenium.")
    return urls

def filter_urls(urls, keep_patterns = [], skip_patterns = [], site_metadata = {}):
    """
    Filter URLs based on keep and skip patterns.
    - If keep_patterns is empty, keep all URLs by default.
    - Always skip URLs matching skip_patterns.
    """
    filtered = []
    for url in urls:
        url_lower = url.lower()  # normalize for case-insensitive matching

        # Skip check
        if any(skip.lower() in url_lower for skip in skip_patterns):
            site_metadata["total_pages_skipped"] += 1

        # Keep check: only if keep_patterns is not empty
        if keep_patterns:
            if any(keep.lower() in url_lower for keep in keep_patterns):
                filtered.append(url)
            else:
                site_metadata["total_pages_skipped"] += 1
        else:
            # If no keep_patterns, keep all URLs (except skipped)
            filtered.append(url)

    return filtered

def crawl_and_save(urls, max_articles = 5, safe_folder = "", extraction_method = "article", extraction_config = [], keep_keywords = [], skip_keywords = [], site_metadata = {}):
    """
    Crawl all URLS.
    """
    for i, url in enumerate(urls[:max_articles]):
        print(f"Crawling {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve URL: {url}")
            site_metadata["total_pages_failed"] += 1
            continue
        try:
            article = Article(url)
            article.download()
            article.parse()

            safe_title = article.title.replace(" ", "_").replace("/", "")
            filename = f"{FOLDER_NAME}/{safe_folder}/{safe_title}.txt"

            if extraction_method == "article":
                if (crawl_article(url, article)) == "":
                        print(f"No text extracted from {url} using article method, skipping save.")
                else:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(crawl_article(url, article))
                        site_metadata["total_pages_saved"] += 1
                        site_metadata["page_lengths"].append(len(crawl_article(url, article)))
            
            elif extraction_method == "class_based":
                extracted_text = crawl_class_based(url, class_names=extraction_config, keep_keywords=keep_keywords, skip_keywords=skip_keywords)
                if extracted_text == "":
                    print(f"No text extracted from {url} using class_based method with classes {extraction_config}, skipping save.")
                else:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(extracted_text)
                        site_metadata["total_pages_saved"] += 1
                        site_metadata["page_lengths"].append(len(extracted_text))

            elif extraction_method == "paragraphs":
                extracted_text = crawl_paragraphs(url, keep_keywords=keep_keywords, skip_keywords=skip_keywords)
                if extracted_text == "":
                    print(f"No text extracted from {url} using paragraphs method, skipping save.")
                else:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(extracted_text)
                        site_metadata["total_pages_saved"] += 1
                        site_metadata["page_lengths"].append(len(extracted_text))

            else:
                print(f"Unknown extraction method: {extraction_method}")
                continue

            print(f"Saved {filename}")
        except Exception as e:
            print("Error:", e)

        time.sleep(random.uniform(0.5,1))  

def crawl_article(url, article, site_metadata = {}):
    """
    Crawl a single article URL and return the extracted text.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()

        # Convert to lowercase for case-insensitive matching
        text = article.text
        lower_text = text.lower()
        
        return article.text
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        site_metadata["total_pages_failed"] += 1
        return ""
    
def crawl_class_based(url, class_names = [], keep_keywords = [], skip_keywords = [], site_metadata = {}):
    """
    Crawl a single URL and extract text based on specified class names and keyword filters.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve URL: {url}")
            return ""

        soup = BeautifulSoup(response.content, "html.parser")

        for class_name in class_names:
            content_divs = soup.find_all("div", class_=class_name)

            if content_divs:
                clean_parts = []

                for div in content_divs:
                    text = div.get_text(separator="\n").strip()

                    link_text = " ".join(a.get_text() for a in div.find_all("a"))

                    # Avoid division by zero
                    if len(text) == 0:
                        continue

                    link_ratio = len(link_text) / len(text)

                    # Skip if more than 40% of text is links
                    if link_ratio > 0.4:
                        continue

                    # Convert to lowercase for case-insensitive matching
                    lower_text = text.lower()

                    # Skip if any unwanted keyword appears
                    if any(keyword in lower_text for keyword in skip_keywords):
                        continue

                    if keep_keywords:
                        if any(keyword in lower_text for keyword in keep_keywords):
                            clean_parts.append(text)
                    else:
                        clean_parts.append(text)

                final_text = "\n".join(clean_parts)
                return final_text

        print(f"No content found with specified classes: {class_names}")
        return ""
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        site_metadata["total_pages_failed"] += 1
        return ""
    
def crawl_paragraphs(url, keep_keywords = [], skip_keywords = [], site_metadata = {}):
    """
    Crawl a single URL and extract text from paragraphs based on keyword filters.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve URL: {url}")
            return ""

        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")

        if paragraphs:
                clean_parts = []

                for p in paragraphs:
                    text = p.get_text(separator="\n").strip()
                    link_text = " ".join(a.get_text() for a in p.find_all("a"))

                    # Avoid division by zero
                    if len(text) == 0:
                        continue

                    link_ratio = len(link_text) / len(text)

                    # Skip if more than 40% of text is links
                    if link_ratio > 0.4:
                        continue

                    # Convert to lowercase for case-insensitive matching
                    lower_text = text.lower()

                    # Skip if any unwanted keyword appears
                    if any(keyword in lower_text for keyword in skip_keywords):
                        continue

                    if keep_keywords:
                        if any(keyword in lower_text for keyword in keep_keywords):
                            clean_parts.append(text)
                    else:
                        clean_parts.append(text)

                final_text = "\n".join(clean_parts)
                return final_text

        print("No paragraphs found")
        return ""
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        site_metadata["total_pages_failed"] += 1
        return ""
    
def crawl_site(site):
    """
    Crawl one site using the site configuration.
    """
    start_time = time.time()
    print(f"\n=== Crawling site: {site['name']} ===")
    site_metadata = {
        "site_urls": site["sites"],
        "total_pages_found": 0,
        "total_pages_failed": 0,
        "total_pages_skipped": 0,
        "total_pages_saved": 0,
        "crawl_duration_seconds": 0,
        "page_lengths": []
        }
    safe_folder = site["name"].replace(" ", "_").replace("/", "")
    os.makedirs(f"{FOLDER_NAME}/{safe_folder}", exist_ok=True)
    
    if site["fetch_method"] == "sitemap":
        all_urls = []
        for sitemap_url in site["sites"]:
            all_urls += fetch_sitemap_urls(sitemap_url, site_metadata)

        print(f"Found {len(all_urls)} URLs in sitemaps")
        filtered_urls = filter_urls(all_urls, site.get("url_include", []),
                                    site.get("url_exclude", []), site_metadata)
        print(f"{len(filtered_urls)} URLs after filtering")

        crawl_and_save(filtered_urls, MAX_PAGES_PER_SITE, safe_folder,
                       site.get("extraction_method", "article"), site.get("extraction_config", []),
                       site.get("keep_keywords", []), site.get("skip_keywords", []), site_metadata)
        
        if site_metadata["total_pages_saved"] >= MAX_PAGES_PER_SITE:
            print("Reached page limit, stopping crawl.")
    
    if site["fetch_method"] == "recursive":
        for start_url in site["sites"]:
            fetch_recursive_urls(start_url, safe_folder, site.get("use_selenium", False), site.get("extraction_method", "article"),site.get("extraction_config", []), site.get("keep_keywords", []), site.get("skip_keywords", []), site_metadata)
            
    print(f"Site crawl completed: {site['name']}")
    site_metadata["average_page_length"] = sum(site_metadata["page_lengths"]) / len(site_metadata["page_lengths"]) if site_metadata["page_lengths"] else 0
    site_metadata["crawl_duration_seconds"] = time.time() - start_time

    site_metadata_title = safe_folder + "_metadata"
    site_metadata_file = f"{FOLDER_NAME}/{safe_folder}/{site_metadata_title}.txt"
    with open(site_metadata_file, "w") as f:
        f.write(str(site_metadata))

    print(f"Metadata for {site['name']}: {site_metadata}")
    return site_metadata

def main():

    sites = [
    {
        "name": "International Alliance ALS MND Association",  # used for folder naming
        "sites": [
            "https://www.als-mnd.org/page.xml"
        ],
        "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
        "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
        "extraction_method": "article",  # use newspaper3k's article extraction
        "extraction_config": [
            # could add config options here if needed, e.g. language, fetch_images, etc.
        ],
        "keep_keywords": [],  # not used for article extraction
        "skip_keywords": [],  # not used for article extraction
        "url_include": ["/support-for-pals-cals/", "/support-for-health-professionals/"],  # keep only these
        "url_exclude": [],  # skip URLs containing these
    },

    {
        "name": "Your ALS Guide",  
        "sites": [
            "https://www.youralsguide.com/sitemap.xml"
        ],
        "fetch_method": "sitemap",
        "use_selenium": False,  
        "extraction_method": "class_based",  
        "extraction_config": ["paragraph"],  # for class_based, this would be a list of class names to try for extraction
        "keep_keywords": [],  # if any of these keywords appear in the extracted text, keep the article
        "skip_keywords": ["newsletter", "coping with the diagnosis", "copyright", "privacy policy"],  # if any of these keywords appear in the extracted text, skip the article
        "url_include": [],  
        "url_exclude": ["/our-story", "/mynas-story", "/newsletter", "/testimonials", "/licensing", "/contact-us"]    
    },

    {
        "name": "ALS Canada",  
        "sites": [
            "https://als.ca/page-sitemap.xml",
            "https://als.ca/resource-sitemap.xml"
        ],
        "fetch_method": "sitemap",
        "use_selenium": False,
        "extraction_method": "article",  
        "extraction_config": [],
        "keep_keywords": [],  
        "skip_keywords": [], 
        "url_include": ["/what-is-als/", "/managing-als/", "/resource/"],  
        "url_exclude": []    
    },

    {
        "name": "ALS Wiki",  
        "sites": [
            "https://www.alswiki.org/en/about-als",
            "https://www.alswiki.org/en/living-with-als",
            "https://www.alswiki.org/en/care",
            "https://www.alswiki.org/en/adaptive-equipment",
            "https://www.alswiki.org/en/research-and-treatments"
        ],
        "fetch_method": "recursive",
        "use_selenium": False,
        "extraction_method": "article",  
        "extraction_config": [],
        "keep_keywords": [],  
        "skip_keywords": [], 
        "url_include": ["/about-als/", "/living-with-als/", "/care/", "/adaptive-equipment/", "/research-and-treatments/"],  
        "url_exclude": []    
    },

    {
        "name": "IMNDA",  
        "sites": [
            "https://www.imnda.ie/about-mnd",
            "https://www.imnda.ie/just-diagnosed",
            "https://www.imnda.ie/living-with-mnd"
        ],
        "fetch_method": "recursive",
        "use_selenium": True,  # this site has some JS-heavy pages where links are generated dynamically, so we will use Selenium as a fallback for those pages
        "extraction_method": "article",  
        "extraction_config": [],
        "keep_keywords": [],  
        "skip_keywords": [], 
        "url_include": ["/about-mnd/", "/just-diagnosed/", "/living-with-mnd/"],  
        "url_exclude": []    
    },
    
    ]

    all_sites_metadata = {}
    all_site_metadata_file = f"{FOLDER_NAME}/all_sites_metadata.txt"

    for site in sites:
        all_sites_metadata[site['name']] = crawl_site(site)
    
    with open(all_site_metadata_file, "w") as f:
        f.write(str(all_sites_metadata))
        
    print("\nAll done!")

if __name__ == "__main__":
    main()