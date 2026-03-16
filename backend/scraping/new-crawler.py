from pathlib import Path
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
import polars as pl
import lxml.html


def get_base_domain(url_or_netloc):
    """
    Extract the base domain from a URL or netloc string.
    e.g. 'eu.usatoday.com' -> 'usatoday.com'
         'www.usatoday.com' -> 'usatoday.com'
         'https://eu.usatoday.com/path' -> 'usatoday.com'
    """
    netloc = url_or_netloc
    if "://" in netloc:
        netloc = urlparse(netloc).netloc
    parts = netloc.split(".")
    # Return last two parts (handles .com, .org, etc.)
    # For co.uk style TLDs this is imperfect but fine for news sites
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return netloc

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive"
}

# Create folder to store articles
OUTPUT_DIR = Path(__file__).parent / "output"
MAX_PAGES_PER_SITE = 1000

def get_cached_html(url, output_dir, site_metadata=None):
    """
    Get HTML for a URL, using cached version from raw_html folder if available.
    Downloads and caches the HTML if not found locally.
    Returns (html_content, from_cache) tuple, or (None, False) on failure.
    """
    raw_html_dir = os.path.join(output_dir, "raw_html")
    safe_filename = re.sub(r'[^\w\-.]', '_', urlparse(url).path.strip('/'))[:150] or 'index'
    raw_html_path = os.path.join(raw_html_dir, f"{safe_filename}.html")
    
    if os.path.exists(raw_html_path):
        print(f"  Using cached HTML for {url}")
        with open(raw_html_path, "r", encoding="utf-8") as f:
            return f.read(), True
    
    # Download if not cached
    try:
        print(f"  Downloading HTML for {url}")
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve URL: {url}")
            if site_metadata:
                site_metadata["total_pages_failed"] += 1
            return None, False
        
        # Save raw HTML for future use
        os.makedirs(raw_html_dir, exist_ok=True)
        with open(raw_html_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        return response.text, False
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        if site_metadata:
            site_metadata["total_pages_failed"] += 1
        return None, False

def fetch_sitemap_urls(sitemap_url, site_metadata):

    """
    Recursively fetch all URLs from a sitemap or sitemap index.
    """
    urls = []
    try:
        response = requests.get(sitemap_url, timeout=10, headers=headers)
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
                if len(urls) > MAX_PAGES_PER_SITE:
                    break
    except Exception as e:
        site_metadata["total_pages_failed"] += 1
        print(f"Failed to fetch sitemap {sitemap_url}: {e}")
    return urls

def fetch_recursive_urls(start_url, use_selenium = False, extraction_method = "article", extraction_config = [], keep_keywords = [], skip_keywords = [], site_metadata = {}, output_dir = OUTPUT_DIR, limit_depth = False, max_depth = 3):

    """
    Recursively fetch URLs starting from start_url, staying within base_domain.
    
    Args:
        limit_depth: If True, limits how deep the crawler follows links.
        max_depth:   Maximum depth to crawl (only used when limit_depth is True).
                     Depth 0 = the start_url itself, depth 1 = links found on start_url, etc.
    """
    visited = set()
    to_visit = [(start_url, 0)]  # (url, depth) tuples
    urls = []

    # Track the depth at which each URL was discovered
    if "url_depths" not in site_metadata:
        site_metadata["url_depths"] = {}  # url -> depth
    if "max_depth_reached" not in site_metadata:
        site_metadata["max_depth_reached"] = 0

    df = pl.DataFrame({"url": pl.Series([], dtype=pl.String), "title": pl.Series([], dtype=pl.String), "path": pl.Series([], dtype=pl.String), "text": pl.Series([], dtype=pl.String)})

    while to_visit:
        if site_metadata["total_pages_saved"] >= MAX_PAGES_PER_SITE:
            print("Reached page limit, stopping crawl.")
            break
        url, depth = to_visit.pop()

        if url in visited:
            continue

        # Enforce depth limit
        if limit_depth and depth > max_depth:
            site_metadata["total_pages_skipped"] += 1
            continue

        print(f"Visiting (depth {depth}): {url}")
        visited.add(url)
        urls.append(url)
        site_metadata["total_pages_found"] += 1
        site_metadata["url_depths"][url] = depth
        site_metadata["max_depth_reached"] = max(site_metadata["max_depth_reached"], depth)
        
        df_ = crawl_and_save([url], 1, extraction_method, extraction_config, keep_keywords, skip_keywords, site_metadata, output_dir)  # crawl and save as we go to avoid losing data if crawl is interrupted
        df = pl.concat([df, df_])

        # Skip link discovery if we've hit the depth limit
        if limit_depth and depth >= max_depth:
            continue

        html_for_links, _ = get_cached_html(url, output_dir)
        if html_for_links is None:
            print("Failed to get HTML for link discovery:", url)
            continue

        soup = BeautifulSoup(html_for_links, "html.parser")

        find_link = 0
        child_depth = depth + 1
        start_base_domain = get_base_domain(start_url)
        for link in soup.find_all("a", href=True):
            href = link["href"]

            full_url = urljoin(url, href)
            full_url = full_url.split("#")[0]  # remove fragment

            parsed = urlparse(full_url)

            if full_url in visited:
                continue

            # Compare base domains so eu.usatoday.com links to www.usatoday.com still match
            if get_base_domain(parsed.netloc) != start_base_domain:
                continue

            # if not full_url.startswith(start_url):
            #     site_metadata["total_pages_skipped"] += 1
            #     continue

            find_link+=1
            to_visit.append((full_url, child_depth))

        if use_selenium and find_link <= 1:  # heuristic: if we found very few links, maybe it's a JS-heavy page where links are generated dynamically and not present in the initial HTML
            print(f"No new links found on {url} using standard method.")
            selenium_urls = fetch_selenium_urls(start_url, url, visited, site_metadata)
            to_visit.extend([(u, child_depth) for u in selenium_urls])  # try Selenium as fallback for JS-heavy pages

    return df

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

            if get_base_domain(parsed.netloc) != get_base_domain(page_url):
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
            continue

        if url.endswith((".jpg", ".jpeg", ".png", ".gif")):
            site_metadata["total_pages_skipped"] += 1
            continue

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

def crawl_and_save(urls, max_articles = 5, extraction_method = "article", extraction_config = [], keep_keywords = [], skip_keywords = [], site_metadata = {}, output_dir = OUTPUT_DIR):
    """
    Crawl all URLS.
    """
    data = {"url": [], "title": [], "path": [], "text": []}

    for i, url in enumerate(urls[:max_articles]):
        print(f"Crawling {url}")
        
        html, from_cache = get_cached_html(url, output_dir, site_metadata)
        if html is None:
            continue

        try:
            article = Article(url)
            article.set_html(html)
            article.parse()

            if extraction_method == "article":
                paths, sections = crawl_article(url, html, keep_keywords=keep_keywords, skip_keywords=skip_keywords)
                if not sections:
                    print(f"No text extracted from {url} using article method, skipping save.")
                else:
                    data["url"].extend([url] * len(sections))
                    data["title"].extend([article.title] * len(sections))
                    data["path"].extend(paths)
                    data["text"].extend(sections)
                    site_metadata["total_pages_saved"] += 1
                    site_metadata["page_lengths"].append(len("".join(sections)))
            
            elif extraction_method == "class_based":
                paths, sections = crawl_class_based(url, html, class_names=extraction_config, keep_keywords=keep_keywords, skip_keywords=skip_keywords)
                if not sections:
                    print(f"No text extracted from {url} using class_based method with classes {extraction_config}, skipping save.")
                else:
                    data["url"].extend([url] * len(sections))
                    data["title"].extend([article.title] * len(sections))
                    data["path"].extend(paths)
                    data["text"].extend(sections)
                    site_metadata["total_pages_saved"] += 1
                    site_metadata["page_lengths"].append(len("".join(sections)))

            elif extraction_method == "paragraphs":
                paths, sections = crawl_paragraphs(url, html, keep_keywords=keep_keywords, skip_keywords=skip_keywords)
                if not sections:
                    print(f"No text extracted from {url} using paragraphs method, skipping save.")
                else:
                    data["url"].extend([url] * len(sections))
                    data["title"].extend([article.title] * len(sections))
                    data["path"].extend(paths)
                    data["text"].extend(sections)
                    site_metadata["total_pages_saved"] += 1
                    site_metadata["page_lengths"].append(len("".join(sections)))

            else:
                print(f"Unknown extraction method: {extraction_method}")
                continue

            print(f"Saved {url}")
        except Exception as e:
            print("Error:", e)

        if not from_cache:
            time.sleep(random.uniform(0.5,1))
    
    if not data["url"]:  # return empty dataframe with correct schema if no data was saved
        return pl.DataFrame({"url": pl.Series([], dtype=pl.String), "title": pl.Series([], dtype=pl.String), "path": pl.Series([], dtype=pl.String), "text": pl.Series([], dtype=pl.String)})

    return pl.DataFrame(data)

def extract_text_with_heading_paths(elements, keep_keywords = [], skip_keywords = []):
    """
    Extract text from a list of BeautifulSoup elements, preserving the heading
    hierarchy as a path prefix (e.g. "Heading > Subheading") for each section.
    Same approach as clean.py.
    """
    paths = []
    sections = []
    current_path = []
    current_levels = []
    current_text = []

    def flush_section():
        nonlocal paths, sections
        if not current_text:
            return
        section_text = "\n".join(current_text).strip()
        if section_text:
            paths.append(" > ".join(current_path))
            sections.append(section_text)
        current_text.clear()

    for el in elements:
        tag_name = el.name or ""

        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            flush_section()

            level = int(tag_name[1])
            heading = el.get_text(separator=" ", strip=True)

            # Adjust path - pop headings at same or deeper level
            while current_levels and current_levels[-1] >= level:
                current_levels.pop()
                current_path.pop()

            current_levels.append(level)
            current_path.append(heading)

        elif tag_name in ["p", "ul", "ol"]:
            if tag_name in ["ul", "ol"]:
                el_text = el.get_text(separator="\n", strip=True)
            else:
                el_text = el.get_text(separator=" ", strip=True)

            if not el_text:
                continue

            # Skip if link-heavy
            # link_text = " ".join(a.get_text() for a in el.find_all("a"))
            # if len(link_text) / len(el_text) > 0.8: # heuristic: if more than 80% of the text is from links, it's probably a nav menu or similar
            #     continue

            lower_text = el_text.lower()

            # Skip if any unwanted keyword appears
            if any(kw.lower() in lower_text for kw in skip_keywords):
                continue

            # Keep check: only if keep_keywords is not empty
            if keep_keywords and not any(kw.lower() in lower_text for kw in keep_keywords):
                continue

            current_text.append(el_text)

    flush_section()
    return paths, sections


def crawl_article(url, html, keep_keywords = [], skip_keywords = [], site_metadata = {}):
    """
    Extract text from pre-fetched HTML content, preserving heading paths.
    Uses newspaper3k's top_node for content area detection, then parses
    headings/paragraphs with BeautifulSoup to preserve structure.
    """
    try:
        article = Article(url)
        article.set_html(html)
        article.parse()

        # Use newspaper3k's detected content area if available
        if article.top_node is not None:
            print("Using newspaper3k's top_node.")
            top_html = lxml.html.tostring(article.top_node, encoding="unicode")
            content = BeautifulSoup(top_html, "html.parser")
        else:
            soup = BeautifulSoup(html, "html.parser")
            content = (soup.find("article") or soup.find("main") or
                       soup.find("div", role="main") or soup.find("body") or soup)

        elements = content.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol"])
        return extract_text_with_heading_paths(elements, keep_keywords, skip_keywords)
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        site_metadata["total_pages_failed"] += 1
        return ""
    
def crawl_class_based(url, html, class_names = [], keep_keywords = [], skip_keywords = [], site_metadata = {}):
    """
    Extract text from pre-fetched HTML based on specified class names, preserving heading paths.
    Handles sites where headings are siblings of the class containers, and where
    text may be in nested <span> elements rather than <p> tags.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        for class_name in class_names:
            content_divs = soup.find_all(class_=class_name)

            if not content_divs:
                continue

            # Find the common parent that contains all matched elements
            # so we can also capture sibling headings
            first_parent = content_divs[0].parent
            
            # Collect all relevant elements in document order from the parent:
            # headings (siblings of the class containers) + content from the containers
            all_elements = []
            
            if first_parent:
                for child in first_parent.children:
                    if not hasattr(child, 'name') or child.name is None:
                        continue
                    
                    # Include headings directly (they're siblings of the class containers)
                    if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        all_elements.append(child)
                    
                    # For elements with the target class, extract their content
                    elif class_name in (child.get("class") or []):
                        # Look for standard content elements inside
                        inner = child.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol"])
                        if inner:
                            all_elements.extend(inner)
                        else:
                            # No <p> tags — text is likely in <span> or direct text nodes
                            # Extract text and wrap as a synthetic <p>
                            text = child.get_text(separator=" ", strip=True)
                            if text:
                                fake_p = soup.new_tag("p")
                                fake_p.string = text
                                all_elements.append(fake_p)
            
            if not all_elements:
                # Fallback: just extract from inside the matched divs (original approach)
                for div in content_divs:
                    inner = div.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol"])
                    if inner:
                        all_elements.extend(inner)
                    else:
                        text = div.get_text(separator=" ", strip=True)
                        if text:
                            fake_p = soup.new_tag("p")
                            fake_p.string = text
                            all_elements.append(fake_p)

            result = extract_text_with_heading_paths(all_elements, keep_keywords, skip_keywords)
            if result:
                return result

        print(f"No content found with specified classes: {class_names}")
        return ""
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        if site_metadata:
            site_metadata["total_pages_failed"] = site_metadata.get("total_pages_failed", 0) + 1
        return ""
    
def crawl_paragraphs(url, html, keep_keywords = [], skip_keywords = [], site_metadata = {}):
    """
    Extract text from pre-fetched HTML paragraphs, preserving heading paths.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol"])

        if elements:
            return extract_text_with_heading_paths(elements, keep_keywords, skip_keywords)

        print("No content found")
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

    # Create per-site output directory
    safe_site_name = re.sub(r'[^\w\-.]', '_', site['name'])
    site_output_dir = os.path.join(OUTPUT_DIR, safe_site_name)
    os.makedirs(site_output_dir, exist_ok=True)
    os.makedirs(os.path.join(site_output_dir, "raw_html"), exist_ok=True)

    site_metadata = {
        "site_urls": site["sites"],
        "total_pages_found": 0,
        "total_pages_failed": 0,
        "total_pages_skipped": 0,
        "total_pages_saved": 0,
        "crawl_duration_seconds": 0,
        "page_lengths": []
        }

    df = pl.DataFrame({"url": pl.Series([], dtype=pl.String), "title": pl.Series([], dtype=pl.String), "path": pl.Series([], dtype=pl.String), "text": pl.Series([], dtype=pl.String)})
    
    if site["fetch_method"] == "sitemap":
        all_urls = []
        for sitemap_url in site["sites"]:
            all_urls += fetch_sitemap_urls(sitemap_url, site_metadata)

        print(f"Found {len(all_urls)} URLs in sitemaps")
        filtered_urls = filter_urls(all_urls, site.get("url_include", []),
                                    site.get("url_exclude", []), site_metadata)
        print(f"{len(filtered_urls)} URLs after filtering")

        df = crawl_and_save(filtered_urls, MAX_PAGES_PER_SITE,
                       site.get("extraction_method", "article"), site.get("extraction_config", []),
                       site.get("keep_keywords", []), site.get("skip_keywords", []), site_metadata, site_output_dir)
        
        if site_metadata["total_pages_saved"] >= MAX_PAGES_PER_SITE:
            print("Reached page limit, stopping crawl.")
    
    if site["fetch_method"] == "recursive":
        for start_url in site["sites"]:
            df_ = fetch_recursive_urls(
                start_url,
                use_selenium=site.get("use_selenium", False),
                extraction_method=site.get("extraction_method", "article"),
                extraction_config=site.get("extraction_config", []),
                keep_keywords=site.get("keep_keywords", []),
                skip_keywords=site.get("skip_keywords", []),
                site_metadata=site_metadata,
                output_dir=site_output_dir,
                limit_depth=site.get("limit_depth", False),
                max_depth=site.get("max_depth", 3),
            )
            df = pl.concat([df, df_])
            
    print(f"Site crawl completed: {site['name']}")
    site_metadata["average_page_length"] = sum(site_metadata["page_lengths"]) / len(site_metadata["page_lengths"]) if site_metadata["page_lengths"] else 0
    site_metadata["crawl_duration_seconds"] = time.time() - start_time

    # Summarise depth distribution
    url_depths = site_metadata.get("url_depths", {})
    if url_depths:
        depth_counts = {}
        for d in url_depths.values():
            depth_counts[d] = depth_counts.get(d, 0) + 1
        site_metadata["depth_distribution"] = dict(sorted(depth_counts.items()))
        site_metadata["max_depth_reached"] = max(url_depths.values())
    # Remove per-url depth map from the summary file to keep it readable
    site_metadata.pop("url_depths", None)

    output_csv = os.path.join(site_output_dir, f"{safe_site_name}.csv")
    df.write_csv(output_csv)

    site_metadata_file = os.path.join(site_output_dir, f"{safe_site_name}_metadata.txt")
    with open(site_metadata_file, "w") as f:
        f.write(str(site_metadata))

    print(f"Metadata for {site['name']}: {site_metadata}")
    return site_metadata

def main():

    sites = [

#         {
#         "name": "USA Today",
#         "sites": [
#     "https://eu.usatoday.com/sitemap/2026/february/1",
#     "https://eu.usatoday.com/sitemap/2026/february/2",
#     "https://eu.usatoday.com/sitemap/2026/february/3",
#     "https://eu.usatoday.com/sitemap/2026/february/4",
#     "https://eu.usatoday.com/sitemap/2026/february/5",
#     "https://eu.usatoday.com/sitemap/2026/february/6",
#     "https://eu.usatoday.com/sitemap/2026/february/7",
#     "https://eu.usatoday.com/sitemap/2026/february/8",
#     "https://eu.usatoday.com/sitemap/2026/february/9",
#     "https://eu.usatoday.com/sitemap/2026/february/10",
#     "https://eu.usatoday.com/sitemap/2026/february/11",
#     "https://eu.usatoday.com/sitemap/2026/february/12",
#     "https://eu.usatoday.com/sitemap/2026/february/13",
#     "https://eu.usatoday.com/sitemap/2026/february/14",
#     "https://eu.usatoday.com/sitemap/2026/february/15",
#     "https://eu.usatoday.com/sitemap/2026/february/16",
#     "https://eu.usatoday.com/sitemap/2026/february/17",
#     "https://eu.usatoday.com/sitemap/2026/february/18",
#     "https://eu.usatoday.com/sitemap/2026/february/19",
#     "https://eu.usatoday.com/sitemap/2026/february/20",
#     "https://eu.usatoday.com/sitemap/2026/february/21",
#     "https://eu.usatoday.com/sitemap/2026/february/22",
#     "https://eu.usatoday.com/sitemap/2026/february/23",
#     "https://eu.usatoday.com/sitemap/2026/february/24",
#     "https://eu.usatoday.com/sitemap/2026/february/25",
#     "https://eu.usatoday.com/sitemap/2026/february/26",
#     "https://eu.usatoday.com/sitemap/2026/february/27",
#     "https://eu.usatoday.com/sitemap/2026/february/28"
# ],
#         "fetch_method": "recursive",  # currently only sitemap is implemented, but could add direct crawling later
#         "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
#         "limit_depth": True,    # whether to limit the depth of the recursive crawl
#         "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
#         "extraction_method": "article",  # use newspaper3k's article extraction
#         "extraction_config": [
#             # could add config options here if needed, e.g. language, fetch_images, etc.
#         ],
#         "keep_keywords": [],  # not used for article extraction
#         "skip_keywords": [],  # not used for article extraction
#         "url_include": [],  # keep only these
#         "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
#     },
    #  {
    #     "name": "Fox News",
    #     "sites": [
    #         "https://www.foxnews.com/sitemap.xml?type=news",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # }

    #     {
    #     "name": "AP news",
    #     "sites": [
    #         "https://apnews.com/news-sitemap-content.xml",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # },

    # {
    #     "name": "Washington Post",
    #     "sites": [
    #         "https://www.washingtonpost.com/sitemaps/news-sitemap.xml.gz",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # },

    # {
    #     "name": "Snopes",
    #     "sites": [
    #         "https://media.snopes.com/sitemaps/sitemap-news.xml",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # },

    # {
    #     "name": "Wall Street Journal",
    #     "sites": [
    #         "https://www.wsj.com/live_news_sitemap.xml",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # },

    # {
    #     "name": "New York Post",
    #     "sites": [
    #         "https://nypost.com/news-sitemap.xml",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # }

    # {
    #     "name": "MS NOW",
    #     "sites": [
    #         "https://www.ms.now/post-sitemap101.xml",
    #         "https://www.ms.now/post-sitemap100.xml",
    #     ],
    #     "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
    #     "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
    #     "limit_depth": False,    # whether to limit the depth of the recursive crawl
    #     "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
    #     "extraction_method": "article",  # use newspaper3k's article extraction
    #     "extraction_config": [
    #         # could add config options here if needed, e.g. language, fetch_images, etc.
    #     ],
    #     "keep_keywords": [],  # not used for article extraction
    #     "skip_keywords": [],  # not used for article extraction
    #     "url_include": [],  # keep only these
    #     "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    # },

    {
        "name": "The Onion",
        "sites": [
            "https://theonion.com/post-sitemap58.xml",
        ],
        "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
        "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
        "limit_depth": False,    # whether to limit the depth of the recursive crawl
        "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
        "extraction_method": "article",  # use newspaper3k's article extraction
        "extraction_config": [
            # could add config options here if needed, e.g. language, fetch_images, etc.
        ],
        "keep_keywords": [],  # not used for article extraction
        "skip_keywords": [],  # not used for article extraction
        "url_include": [],  # keep only these
        "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    },

    {
        "name": "The Gateway Pundit",
        "sites": [
            "https://www.thegatewaypundit.com/news-sitemap.xml",
            "https://www.thegatewaypundit.com/post-sitemap182.xml"
        ],
        "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
        "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
        "limit_depth": False,    # whether to limit the depth of the recursive crawl
        "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
        "extraction_method": "article",  # use newspaper3k's article extraction
        "extraction_config": [
            # could add config options here if needed, e.g. language, fetch_images, etc.
        ],
        "keep_keywords": [],  # not used for article extraction
        "skip_keywords": [],  # not used for article extraction
        "url_include": [],  # keep only these
        "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    },

     {
        "name": "Daily mail",
        "sites": [
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-28.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-27.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-26.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-25.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-24.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-23.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-22.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-21.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-20.xml",
            "https://www.dailymail.co.uk/sitemap-articles-day~2026-02-19.xml",
        ],
        "fetch_method": "sitemap",  # currently only sitemap is implemented, but could add direct crawling later
        "use_selenium": False,  # whether to use Selenium for JS-heavy pages (not implemented in this version, but could add later)
        "limit_depth": False,    # whether to limit the depth of the recursive crawl
        "max_depth": 1,         # depth 0 = start URL, 1 = links on start URL, 2 = links on those pages
        "extraction_method": "article",  # use newspaper3k's article extraction
        "extraction_config": [
            # could add config options here if needed, e.g. language, fetch_images, etc.
        ],
        "keep_keywords": [],  # not used for article extraction
        "skip_keywords": [],  # not used for article extraction
        "url_include": [],  # keep only these
        "url_exclude": ["/sport/", "/sports/", "/football", "/terms", "/about-your-subscription", "/index", "/privacy", "/sitemap"],  # skip URLs containing these
    },
    
    ]

    all_sites_metadata = {}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_site_metadata_file = os.path.join(OUTPUT_DIR, "all_sites_metadata.txt")

    for site in sites:
        all_sites_metadata[site['name']] = crawl_site(site)
    
    with open(all_site_metadata_file, "w") as f:
        f.write(str(all_sites_metadata))
        
    print("\nAll done!")

if __name__ == "__main__":
    main()