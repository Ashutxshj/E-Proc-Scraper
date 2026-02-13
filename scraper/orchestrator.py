"""
Main orchestrator that coordinates fetching, parsing, cleaning, and persistence
"""
from models.tender import Tender
from models.run_metadata import RunMetadata
from scraper.fetcher import Fetcher
from scraper.parser import Parser
from scraper.cleaner import Cleaner
from scraper.persister import Persister
from utils.logger import RunLogger
from config.settings import (
    BASE_URL, SCRAPER_VERSION, RATE_LIMIT, 
    CONCURRENCY, DEFAULT_LIMIT, OUTPUT_PATH, METADATA_DB,
    TENDER_LIST_ENDPOINT  # Import the new endpoint
)


class Orchestrator:
    """Coordinates the entire scraping workflow"""

    def __init__(
        self,
        limit: int = DEFAULT_LIMIT,
        rate_limit: float = RATE_LIMIT,
        concurrency: int = CONCURRENCY,
        output_path: str = OUTPUT_PATH,
        metadata_db: str = METADATA_DB
    ):
        # Create run metadata
        self.metadata = RunMetadata.create_new(
            scraper_version=SCRAPER_VERSION,
            config={
                "limit": limit,
                "rate_limit": rate_limit,
                "concurrency": concurrency,
                "output_path": output_path,
                "metadata_db": metadata_db
            }
        )

        # Initialize logger with run_id
        self.logger = RunLogger(self.metadata.run_id)

        # Initialize components
        self.fetcher = Fetcher(self.logger, rate_limit=rate_limit)
        self.parser = Parser(self.logger)
        self.cleaner = Cleaner(self.logger)
        self.persister = Persister(self.logger, output_path, metadata_db)

        self.limit = limit
        self.logger.info(f"Initialized scraper with limit={limit}, rate_limit={rate_limit}")

    def run(self):
        """Execute the scraping workflow"""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting scraper run: {self.metadata.run_id}")
        self.logger.info("=" * 60)

        # Use the context manager we added to Fetcher
        try:
            with self.fetcher:
                # Step 1: Fetch tender list via API (XHR)
                self.logger.info("Step 1: Fetching tender list from API...")
                
                # We use fetch_api with POST as discovered in network logs
                # If the API needs a payload, you can pass it here in data={}
                json_data = self.fetcher.fetch_api(TENDER_LIST_ENDPOINT, method="POST")
                self.metadata.pages_visited += 1

                # Step 2: Parse tenders from JSON
                self.logger.info("Step 2: Parsing tenders from JSON response...")
                raw_tenders = self.parser.parse_tender_from_json(json_data)
                self.metadata.tenders_parsed = len(raw_tenders)

                # Limit the number of tenders
                raw_tenders = raw_tenders[:self.limit]
                self.logger.info(f"Limited to {len(raw_tenders)} tenders")

                # Step 3: Clean and normalize tenders
                self.logger.info("Step 3: Cleaning and normalizing tender data...")
                cleaned_tenders = []
                tender_types_set = set()

                for raw_tender in raw_tenders:
                    try:
                        tender = self.cleaner.clean_tender(raw_tender)
                        if tender:
                            cleaned_tenders.append(tender)
                            tender_types_set.add(tender.tender_type)
                    except Exception as e:
                        self.logger.error(f"Error cleaning tender: {e}")
                        self.metadata.failures += 1

                self.metadata.tender_types_processed = list(tender_types_set)
                self.logger.info(f"Cleaned {len(cleaned_tenders)} tenders")

                # Step 4: Persist tenders
                self.logger.info("Step 4: Persisting tender data...")
                saved_count = self.persister.save_tenders(cleaned_tenders)
                self.metadata.tenders_saved = saved_count

                # Calculate deduplication
                self.metadata.deduped_count = len(cleaned_tenders) - saved_count

                # Finish and save metadata
                self.metadata.finish()
                self.persister.save_run_metadata(self.metadata)

                self.logger.info("=" * 60)
                self.logger.info(f"Scraper run completed successfully!")
                self.logger.info(f"  - Tenders parsed: {self.metadata.tenders_parsed}")
                self.logger.info(f"  - Tenders saved: {self.metadata.tenders_saved}")
                self.logger.info(f"  - Duration: {self.metadata.duration_seconds:.2f}s")
                self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Scraper run failed: {e}")
            self.metadata.finish()
            self.metadata.error_summary["fatal_error"] = str(e)
            self.persister.save_run_metadata(self.metadata)
            raise

    def get_metadata(self) -> RunMetadata:
        """Return the run metadata"""
        return self.metadata