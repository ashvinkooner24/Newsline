import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

BASE_DOMAIN ="https://www.alswiki.org/"
START_SECTION = "https://www.alswiki.org/en/living-with-als"

visited = set()
to_visit = [START_SECTION]

while to_visit:
    url = to_visit.pop()

    if url in visited:
        continue

    print("Visiting:", url)
    visited.add(url)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print("Failed:", url)
            continue
    except Exception as e:
        print("Error:", url)
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    # --------- Extract text here if you want ----------
    page_text = soup.get_text(separator="\n").strip()
    # (You could save this to file here)
    # ---------------------------------------------------

    for link in soup.find_all("a", href=True):
        href = link["href"]

        full_url = urljoin(BASE_DOMAIN, href)

        parsed = urlparse(full_url)

        # Only crawl same domain
        if parsed.netloc != urlparse(BASE_DOMAIN).netloc:
            continue

        # Only stay inside the research section
        if not full_url.startswith(START_SECTION):
            continue

        if full_url not in visited:
            to_visit.append(full_url)

    time.sleep(1)  # polite delay