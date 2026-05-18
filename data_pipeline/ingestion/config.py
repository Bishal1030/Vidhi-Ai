import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Directories
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DOCS_DIR = os.path.join(DATA_DIR, "raw_documents")
PROCESSED_TEXT_DIR = os.path.join(DATA_DIR, "processed_text")
STRUCTURED_ACTS_DIR = os.path.join(DATA_DIR, "structured_acts")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure all directories exist
for directory in [DATA_DIR, RAW_DOCS_DIR, PROCESSED_TEXT_DIR, STRUCTURED_ACTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Log file paths
INGESTION_LOG = os.path.join(LOGS_DIR, "ingestion.log")
ERROR_LOG = os.path.join(LOGS_DIR, "error.log")

# Scraping settings
LAW_COMMISSION_BASE_URL = "https://lawcommission.gov.np"
CONSTITUTION_CATEGORY_URL = "https://lawcommission.gov.np/category/1807/"

# Target category configurations to make the scraper generic/extensible
# Category ID -> Name map
CATEGORIES = {
    "1807": "संविधान (Constitution)",
    # We can add other category IDs here for general Acts/Regulations in future
}

# Request headers to look like a standard browser request
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ne;q=0.8",
}

# Ingestion configuration settings
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
