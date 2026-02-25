import random
import time
from typing import Optional
import json
import csv
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    )
}
BASE = "https://en.wikipedia.org"
REQUEST_TIMEOUT = 10
MIN_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 3.0


def _create_session() -> requests.Session:
    """
    Create a requests session with retry and backoff configured.
    Helps avoid bans due to transient failures or rate limiting.
    """
    session = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD", "OPTIONS"),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session


def _respectful_delay() -> None:
    """Sleep a random short interval to reduce request burstiness."""
    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    time.sleep(delay)


def _fetch_html(url: str, session: Optional[requests.Session] = None) -> Optional[BeautifulSoup]:
    """
    Fetch a URL with basic anti-ban measures and verification.

    Returns a BeautifulSoup object on success, or None on failure.
    """
    sess = session or _create_session()

    try:
        response = sess.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        print(f"Request error for {url}: {exc}")
        return None

    # Basic HTTP status verification and soft handling of rate limiting
    if response.status_code == 429:
        print(f"Rate limited (429) when requesting {url}; backing off.")
        _respectful_delay()
        return None

    if response.status_code != 200:
        print(f"Unexpected status {response.status_code} for {url}")
        return None

    if not response.content:
        print(f"Empty response body for {url}")
        return None

    _respectful_delay()

    soup = BeautifulSoup(response.content, "lxml")

    # Simple structural verification to detect unexpected layouts/ban pages
    if soup.find("title") is None:
        print(f"No <title> found for {url}; page may be invalid.")
        return None

    return soup


def scrapeURL() -> None:
    """
    Scrape category page for target links with verification.
    """
    session = _create_session()
    url = "https://en.wikipedia.org/wiki/Category:Tourist_attractions_in_Abu_Dhabi"

    soup = _fetch_html(url, session=session)
    if soup is None:
        print("Failed to fetch or verify category page HTML.")
        return

    content = soup.find("div", attrs={"id": "mw-pages"})
    if content is None:
        print("Could not find 'mw-pages' container; page structure may have changed.")
        return

    content = content.find("div", attrs={"class": "mw-content-ltr"})
    if content is None:
        print("Could not find 'mw-content-ltr' within 'mw-pages'; aborting.")
        return

    pages = content.find_all("a")
    if not pages:
        print("No links found inside category content; possible layout change or block.")
        return

    with open("data/targets.csv", "a", encoding="utf-8") as targets:
        for page in pages:
            href = page.get("href")
            # Basic verification for scraped links
            if not href or not href.startswith("/wiki/"):
                continue

            targets.write(f"{href}\n")
            print(href)


def scrapePage(url: str, session: Optional[requests.Session] = None):
    """
    Scrape a single Wikipedia page for its infobox and raw HTML.

    Includes simple verification that an infobox exists before writing.
    """
    sess = session or _create_session()
    full_url = BASE + url

    soup = _fetch_html(full_url, session=sess)
    if soup is None:
        print(f"Skipping {url}: failed to fetch or verify HTML.")
        return

    # Sanitize URL into a safe file name
    file_name = url.replace("wiki/", "")

    # Store full HTML for debugging/auditing
    with open(f"data/pages/{file_name}.csv", "a", encoding="utf-8") as page:
        page.write(soup.prettify())

    # Extract and verify infobox content
    infobox = soup.find("table", attrs={"class": "infobox"})
    if infobox is None:
        print(f"No infobox found for {url}; skipping structured data write.")
        return

    rows = infobox.find_all("tr")
    if not rows:
        print(f"Infobox for {url} has no rows; skipping structured data write.")
        return

    text_content = infobox.get_text(separator=" ", strip=True)
    if not text_content:
        print(f"Infobox for {url} appears empty after cleanup; skipping.")
        return

    entry = {
        "raw_html":url,
        "name": title.get_text(separator=" ", strip=True),
        "infobox_text":text_content
    }
    return entry

# extracting info without fetching file
def scrapeFile(url: str):
    with open(url, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file,'lxml')
        if not soup:
            print("error")
            return
    title = soup.find("span",attrs={"class":"mw-page-title-main"})
    infobox = soup.find("table",attrs={"class":"infobox"})

    if title is None:
        print(f"No title found for {url}; skipping structured data write.")
        return

    if infobox is None:
        print(f"No infobox found for {url}; skipping structured data write.")
        return

    rows = infobox.find_all("tr")
    if not rows:
        print(f"Infobox for {url} has no rows; skipping structured data write.")
        return

    text_content = infobox.get_text(separator=" ", strip=True)
    if not text_content:
        print(f"Infobox for {url} appears empty after cleanup; skipping.")
        return

    entry = {
        "raw_html":url,
        "name": title.get_text(separator=" ", strip=True),
        "infobox_text":text_content
    }
    return entry
    


def main() -> None:
    # scrape for target urls
    # scrapeURL()

    # scrape each page from targets
    # with open('data/targets.csv', mode='r', encoding='utf-8') as file:
    #     urls = csv.reader(file)
    #     for url in urls:
    #         scrapePage(url[0])


    # parsing entries from html doc (no fetching)
    path = Path("./data/pages")
    data = []
    for item in path.iterdir():
        result = scrapeFile(str(item))
        if(result):
            data.append(result)

    with open("data/raw.json", "a") as f:
        json.dump(data,f,indent=4)

if __name__ == "__main__":
    main()