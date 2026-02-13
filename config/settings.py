import os

# Base URL
BASE_URL = "https://tender.nprocure.com"

# API Endpoints
TENDER_LIST_ENDPOINT = "/beforeLoginTenderTableList"
# Note: Some APIs require the full path if BASE_URL isn't automatically prepended
# TENDER_LIST_URL = "https://tender.nprocure.com/beforeLoginTenderTableList"

# Default API Payload (Update these based on your "Payload" tab in DevTools)
DEFAULT_PAYLOAD = {
    "page": 1,
    "size": 10,
    "search": ""
}

# Rate limiting
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "1.0")) 

# Concurrency
CONCURRENCY = int(os.getenv("CONCURRENCY", "2")) 

# Retry settings
MAX_RETRIES = int(os.getenv("RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))

# Output settings
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output/tenders.json")
METADATA_DB = os.getenv("METADATA_DB", "metadata/runs_metadata.db")

# User Agent
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)

# Ensure output directories exist
os.makedirs("output", exist_ok=True)
os.makedirs("metadata", exist_ok=True)