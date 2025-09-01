# task4.py
# Scrapes "Books to Scrape" with robust selectors and saves a rich CSV.
# Works on Windows with Python 3.13+. Auto-installs missing packages.

import sys, subprocess, importlib

def ensure(pkg, import_name=None):
    """Install a pip package if missing, using the current Python interpreter."""
    name = import_name or pkg
    try:
        importlib.import_module(name)
    except ImportError:
        # ensure pip exists, then install
        try:
            import ensurepip
            ensurepip.bootstrap()
        except Exception:
            pass
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Ensure required packages
ensure("requests")
ensure("beautifulsoup4", "bs4")
ensure("pandas")

import re
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = "https://books.toscrape.com/"
START_URL = urljoin(BASE, "catalogue/page-1.html")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}

def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def rating_to_number(word):
    mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    return mapping.get(word, None)

def parse_book_detail(detail_url):
    """Fetch and parse a single book's detail page."""
    soup = get_soup(detail_url)

    # Title
    title = soup.select_one("div.product_main h1")
    title = title.get_text(strip=True) if title else ""

    # Star rating (word in class list)
    rating_tag = soup.select_one("p.star-rating")
    rating_word = ""
    if rating_tag and rating_tag.has_attr("class"):
        for cls in rating_tag["class"]:
            if cls in {"One", "Two", "Three", "Four", "Five"}:
                rating_word = cls
                break
    rating_num = rating_to_number(rating_word)

    # Availability (and stock count)
    avail = soup.select_one("div.product_main p.availability")
    availability_text = avail.get_text(strip=True) if avail else ""
    stock_match = re.search(r"(\d+)", availability_text)
    stock_count = int(stock_match.group(1)) if stock_match else None

    # Info table (UPC, prices, tax, number of reviews)
    info = {}
    for row in soup.select("table.table.table-striped tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if th and td:
            info[th.get_text(strip=True)] = td.get_text(strip=True)

    upc = info.get("UPC", "")
    price_ex_tax = info.get("Price (excl. tax)", "")
    price_in_tax = info.get("Price (incl. tax)", "")
    num_reviews = info.get("Number of reviews", "")

    # Category (breadcrumb: Home > Books > Category > Title)
    cat = ""
    crumbs = soup.select("ul.breadcrumb li a")
    # Typically: [Home, Books, Category]
    if len(crumbs) >= 3:
        cat = crumbs[-1].get_text(strip=True)  # last <a> before the title (title is not an <a>)
        # On this site sometimes it's the second-to-last link:
        if cat == "Books" and len(crumbs) >= 3:
            cat = crumbs[-2].get_text(strip=True)

    # Description (next sibling of #product_description)
    desc = ""
    desc_header = soup.select_one("#product_description")
    if desc_header:
        p = desc_header.find_next_sibling("p")
        if p:
            desc = p.get_text(" ", strip=True)

    # Image URL
    img = soup.select_one("div.item.active img")
    img_url = urljoin(BASE, img["src"]) if (img and img.has_attr("src")) else ""

    return {
        "Title": title,
        "Category": cat,
        "Price (incl. tax)": price_in_tax,
        "Price (excl. tax)": price_ex_tax,
        "Availability": availability_text,
        "Stock Count": stock_count,
        "Star Rating (word)": rating_word,
        "Star Rating (1-5)": rating_num,
        "Number of Reviews": num_reviews,
        "Description": desc,
        "Product Page URL": detail_url,
        "Image URL": img_url,
        "UPC": upc,
    }

def scrape(max_pages=None, pause=0.4):
    """Scrape listing pages, follow into detail pages, and return list of records."""
    records = []
    page_url = START_URL
    page_num = 0

    while page_url:
        page_num += 1
        if max_pages and page_num > max_pages:
            break

        soup = get_soup(page_url)

        # Each product card
        for card in soup.select("article.product_pod h3 a"):
            href = card.get("href", "")
            detail_url = urljoin(page_url, href)
            # Normalize to absolute URL under /catalogue/
            detail_url = detail_url.replace("../../../", urljoin(BASE, "catalogue/"))
            try:
                rec = parse_book_detail(detail_url)
                records.append(rec)
            except Exception as e:
                # Skip problematic items but continue scraping
                records.append({
                    "Title": "(ERROR parsing item)",
                    "Product Page URL": detail_url,
                    "Error": str(e)
                })
            time.sleep(pause)  # be polite

        # Next page?
        next_link = soup.select_one("li.next a")
        page_url = urljoin(page_url, next_link["href"]) if next_link and next_link.has_attr("href") else None
        time.sleep(pause)

    return records

if __name__ == "__main__":
    # Set to None to crawl ALL pages (≈50); keep 5 to make it quick.
    MAX_PAGES = 5

    data = scrape(max_pages=MAX_PAGES)
    df = pd.DataFrame(data)

    out_name = "task4_products.csv"
    df.to_csv(out_name, index=False, encoding="utf-8-sig")

    print(f"✅ Task 4 completed: Data saved to {out_name}")
    # Show where it was saved for convenience
    import os
    print("Saved at:", os.path.abspath(out_name))
