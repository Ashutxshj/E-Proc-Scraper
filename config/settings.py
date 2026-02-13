"""
Configuration settings for the tender scraper
"""
import os

# Base URL
BASE_URL = "https://tender.nprocure.com"

# API Endpoints (discovered from network inspection)
TENDER_LIST_ENDPOINT = "/beforeLoginTenderTableList"
TENDER_DETAIL_ENDPOINT = "/tender/"

# Rate limiting (requests per second)
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "1.0"))  # 1 request per second

# Concurrency
CONCURRENCY = int(os.getenv("CONCURRENCY", "2"))  # 2 concurrent requests

# Retry settings
MAX_RETRIES = int(os.getenv("RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))

# Output settings
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output/tenders.json")
METADATA_DB = os.getenv("METADATA_DB", "metadata/runs_metadata.db")

# User Agent
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

# Scraper version
SCRAPER_VERSION = "1.0.0"

# Default limit for demo runs
DEFAULT_LIMIT = 50