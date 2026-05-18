import os
import sys
import requests
import re
import urllib.parse
import logging
from typing import Optional

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.config import RAW_DOCS_DIR, DEFAULT_HEADERS, TIMEOUT_SECONDS, INGESTION_LOG, ERROR_LOG

logger = logging.getLogger("fetcher")

def slugify(text: str) -> str:
    """Creates a filesystem-safe slug from a title."""
    # Convert spaces/punctuation to underscores
    slug = re.sub(r'[^\w\s\-\u0900-\u097F]', '', text) # Keep Nepali Unicode chars
    slug = re.sub(r'[\s\-]+', '_', slug).strip('_')
    return slug

def heal_url(url: str) -> list:
    """
    Attempts to generate alternative URLs to heal common typos in Law Commission URLs.
    E.g., correcting '२८१' (missing a zero) to '२०८१'.
    """
    alternatives = []
    
    # 1. Correct २८१ -> २०८१
    if "%E0%A5%A8%E0%A5%AE%E0%A5%A7" in url:
        alt = url.replace("%E0%A5%A8%E0%A5%AE%E0%A5%A7", "%E0%A5%A8%E0%A5%A6%E0%A5%AE%E0%A5%A7")
        alternatives.append(alt)
    elif "२८१" in url:
        alt = url.replace("२८१", "२०८१")
        alternatives.append(alt)
        
    # 2. Correct २०८१ -> २८१ (just in case)
    if "%E0%A5%A8%E0%A5%A6%E0%A5%AE%E0%A5%A7" in url:
        alt = url.replace("%E0%A5%A8%E0%A5%A6%E0%A5%AE%E0%A5%A7", "%E0%A5%A8%E0%A5%AE%E0%A5%A7")
        alternatives.append(alt)
    elif "२०८१" in url:
        alt = url.replace("२०८१", "२८१")
        alternatives.append(alt)

    # 3. Double/single urlencode fixes
    decoded = urllib.parse.unquote(url)
    if decoded != url:
        alternatives.append(decoded)
        
    return alternatives

def download_pdf(pdf_url: str, title: str) -> Optional[str]:
    """
    Downloads a PDF document from pdf_url and saves it to RAW_DOCS_DIR.
    Handles auto-healing of broken/404 URLs for known typos.
    Returns the absolute path to the saved PDF file, or None if download failed.
    """
    if not pdf_url:
        logger.warning(f"No PDF URL provided for title: {title}")
        return None
        
    safe_title = slugify(title)
    file_name = f"{safe_title}.pdf"
    dest_path = os.path.join(RAW_DOCS_DIR, file_name)
    
    # Check if already exists (caching)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024:
        logger.info(f"PDF already exists locally: {dest_path}. Skipping download.")
        return dest_path
        
    urls_to_try = [pdf_url] + heal_url(pdf_url)
    
    for url in urls_to_try:
        logger.info(f"Attempting download from: {url}")
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SECONDS, stream=True)
            if response.status_code == 200:
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Successfully downloaded PDF to {dest_path}")
                return dest_path
            else:
                logger.warning(f"Failed download from {url} with status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading from {url}: {e}")
            
    logger.error(f"Failed to download PDF from all attempted URLs for: {title}")
    with open(ERROR_LOG, "a") as err_f:
        err_f.write(f"Failed to download PDF (Title: {title}) from all URLs: {urls_to_try}\n")
    return None

if __name__ == "__main__":
    # Test downloading the constitution using the scraper-found URL (which is broken)
    # The auto-healer should resolve it to the correct working URL!
    broken_url = "https://giwmscdnone.gov.np/media/pdf_upload/%E0%A4%A8%E0%A5%87%E0%A4%AA%E0%A4%BE%E0%A4%B2%E0%A4%95%E0%A5%8B%20%E0%A4%B8_%E0%A4%82%E0%A4%B5%E0%A4%BF%E0%A4%A7%E0%A4%BE%E0%A4%A8%20unicode%20%E0%A4%AD%E0%A4%BE%E0%A4%A6%E0%A5%8D%E0%A4%B0%20%E0%A5%A8%E0%A5%AE%E0%A5%A7_mtbuyjt.pdf"
    test_title = "नेपालको संविधान"
    path = download_pdf(broken_url, test_title)
    print(f"Downloaded path: {path}")
