import requests
import urllib3
from bs4 import BeautifulSoup
import urllib.parse
import os
import sys
import logging

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.config import LAW_COMMISSION_BASE_URL, CONSTITUTION_CATEGORY_URL, DEFAULT_HEADERS, TIMEOUT_SECONDS, INGESTION_LOG, ERROR_LOG

# Configure loggers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(INGESTION_LOG),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("scraper")

def get_soup(url: str) -> BeautifulSoup:
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SECONDS, verify=False)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        # Log to error.log as well
        with open(ERROR_LOG, "a") as f:
            f.write(f"Error fetching URL {url}: {e}\n")
        raise

def scrape_category(category_url: str) -> list:
    """
    Scrapes a category page on the Nepal Law Commission site to extract legal document metadata.
    Returns a list of dictionaries with keys: title, date, detail_url, pdf_url.
    """
    logger.info(f"Scraping category URL: {category_url}")
    soup = get_soup(category_url)
    
    documents = []
    
    # The table containing documents usually has class or structure table
    tables = soup.find_all("table")
    if not tables:
        logger.warning(f"No tables found on page: {category_url}")
        return documents
    
    # We will parse the first main table
    table = tables[0]
    rows = table.find_all("tr")
    
    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) < 2:
            continue
            
        # The structure is typically:
        # Col 0: S.N. (Serial Number)
        # Col 1: Title & link to detail page
        # Col 2: Date
        # Col 3/4/etc: Download/PDF links
        
        # 1. Extract Title and Detail Link
        title_cell = cells[1]
        title_link = title_cell.find("a")
        title = ""
        detail_url = ""
        
        if title_link:
            title = title_link.get_text(strip=True)
            href = title_link.get("href", "")
            if href:
                detail_url = urllib.parse.urljoin(LAW_COMMISSION_BASE_URL, href)
        else:
            title = title_cell.get_text(strip=True)
            
        if not title:
            continue
            
        # 2. Extract Date
        date = ""
        if len(cells) > 2:
            date = cells[2].get_text(strip=True)
            
        # 3. Extract PDF URL
        pdf_url = ""
        
        # Look for any links inside the row that point to PDFs
        all_links = row.find_all("a")
        for link in all_links:
            href = link.get("href", "")
            if href and ".pdf" in href.lower():
                # Some are absolute, some might be relative
                if href.startswith("http"):
                    pdf_url = href
                else:
                    pdf_url = urllib.parse.urljoin(LAW_COMMISSION_BASE_URL, href)
                break
                
        # If no PDF link in the row, check if any image or icon link has pdf reference
        if not pdf_url:
            for cell in cells[3:]:
                link = cell.find("a")
                if link:
                    href = link.get("href", "")
                    if href:
                        if href.startswith("http"):
                            pdf_url = href
                        else:
                            pdf_url = urllib.parse.urljoin(LAW_COMMISSION_BASE_URL, href)
                        break

        # Check for target="_blank" tags
        if not pdf_url:
            blank_link = row.find("a", target="_blank")
            if blank_link:
                href = blank_link.get("href", "")
                if href and ".pdf" in href.lower():
                    pdf_url = href

        doc_meta = {
            "title": title,
            "date": date,
            "detail_url": detail_url,
            "pdf_url": pdf_url
        }
        
        logger.info(f"Found document: {title} | Date: {date} | PDF: {pdf_url}")
        documents.append(doc_meta)
        
    return documents


