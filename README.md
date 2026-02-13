A production-ready web scraper for extracting tenders from https://tender.nprocure.com/
## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation
pip install -r requirements.txt


### Run the Scraper
python scrape.py

python scrape.py --limit 10

## Project Structure
/
├── scrape.py              # CLI entrypoint
├── requirements.txt       # Dependencies
├── config/
│   └── settings.py       # Configuration
├── scraper/
│   ├── orchestrator.py   # Main workflow
│   ├── fetcher.py        # HTTP + rate limiting
│   ├── parser.py         # HTML parsing
│   ├── cleaner.py        # Data normalization
│   └── persister.py      # Save to JSON + SQLite
├── models/
│   ├── tender.py         # Tender data model
│   └── run_metadata.py   # Metadata model
├── utils/
│   ├── logger.py         # Logging with run_id
│   ├── retry.py          # Exponential backoff
│   └── dedup.py          # Deduplication
├── output/               # Output JSON files
└── metadata/             # SQLite metadata DB