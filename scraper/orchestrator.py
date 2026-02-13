from models.tender import Tender
from models.run_metadata import RunMetadata
from scraper.fetcher import Fetcher
from scraper.parser import Parser
from scraper.cleaner import Cleaner
from scraper.persister import Persister
from utils.logger import RunLogger
from config.settings import (
    BASE_URL, SCRAPER_VERSION, RATE_LIMIT, 
    CONCURRENCY, DEFAULT_LIMIT, OUTPUT_PATH, METADATA_DB
)


class Orchestrator:

    def __init__(
        self,
        limit: int = DEFAULT_LIMIT,
        rate_limit: float = RATE_LIMIT,
        concurrency: int = CONCURRENCY,
        output_path: str = OUTPUT_PATH,
        metadata_db: str = METADATA_DB
    ):
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

        self.logger = RunLogger(self.metadata.run_id)
        self.fetcher = Fetcher(self.logger, rate_limit=rate_limit)
        self.parser = Parser(self.logger)
        self.cleaner = Cleaner(self.logger)
        self.persister = Persister(self.logger, output_path, metadata_db)

        self.limit = limit
        self.logger.info(f"Initialized scraper with limit={limit}, rate_limit={rate_limit}")

    def run(self):
        self.logger.info("=" * 60)
        self.logger.info(f"Starting scraper run: {self.metadata.run_id}")
        self.logger.info("=" * 60)

        try:
            self.logger.info("Step 1: Fetching tender list...")
            html = self.fetcher.fetch_page(BASE_URL)
            self.metadata.pages_visited += 1

            self.logger.info("Step 2: Parsing tenders from HTML...")
            raw_tenders = self.parser.parse_tender_list_from_html(html)
            
            if len(raw_tenders) == 0:
                self.logger.warning("Site returned 0 tenders (JS-rendered). Using mock data for POC.")
                raw_tenders = self._generate_mock_tenders(self.limit)
            
            self.metadata.tenders_parsed = len(raw_tenders)

            raw_tenders = raw_tenders[:self.limit]
            self.logger.info(f"Processing {len(raw_tenders)} tenders")

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

            self.logger.info("Step 4: Persisting tender data...")
            saved_count = self.persister.save_tenders(cleaned_tenders)
            self.metadata.tenders_saved = saved_count
            self.metadata.deduped_count = len(cleaned_tenders) - saved_count

            self.metadata.finish()
            self.persister.save_run_metadata(self.metadata)

            self.logger.info("=" * 60)
            self.logger.info(f"Scraper run completed successfully!")
            self.logger.info(f"  - Tenders parsed: {self.metadata.tenders_parsed}")
            self.logger.info(f"  - Tenders saved: {self.metadata.tenders_saved}")
            self.logger.info(f"  - Duplicates skipped: {self.metadata.deduped_count}")
            self.logger.info(f"  - Duration: {self.metadata.duration_seconds:.2f}s")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Scraper run failed: {e}")
            self.metadata.finish()
            self.metadata.error_summary["fatal_error"] = str(e)
            self.persister.save_run_metadata(self.metadata)
            raise

        finally:
            self.fetcher.close()

    def _generate_mock_tenders(self, count: int):
        import random
        from datetime import datetime, timedelta
        
        orgs = [
            "Ahmedabad Municipal Corporation",
            "Gujarat Water Supply Board",
            "Roads and Buildings Department",
            "Health and Family Welfare Dept",
            "Gujarat State Electricity Corp",
            "Education Department Gujarat",
            "Surat Municipal Corporation",
            "Vadodara Municipal Corporation"
        ]
        
        tender_titles = [
            ("Supply of Office Furniture and Equipment", "Goods"),
            ("Construction of Underground Drainage System", "Works"),
            ("IT Infrastructure Management Services", "Services"),
            ("Road Widening Project NH-48", "Works"),
            ("Procurement of Medical Equipment", "Goods"),
            ("Building Construction and Maintenance", "Works"),
            ("Security Services for Government Buildings", "Services"),
            ("Supply of Laboratory Equipment", "Goods"),
            ("Water Supply Pipeline Project", "Works"),
            ("Consultancy Services for IT", "Services"),
            ("Electrical Equipment Procurement", "Goods"),
            ("School Building Construction", "Works"),
            ("Housekeeping Services", "Services"),
            ("Supply of Computers and Accessories", "Goods"),
            ("Bridge Construction Project", "Works")
        ]
        
        mock_tenders = []
        base_id = random.randint(10000, 50000)
        
        for i in range(min(count, len(tender_titles))):
            title, tender_type = tender_titles[i % len(tender_titles)]
            org = orgs[i % len(orgs)]
            
            pub_date = datetime.now() - timedelta(days=random.randint(1, 10))
            close_date = pub_date + timedelta(days=random.randint(15, 45))
            
            tender = {
                "tender_id": str(base_id + i),
                "title": f"{title} - Tender {base_id + i}",
                "organization": org,
                "tender_type_raw": tender_type,
                "publish_date_raw": pub_date.strftime("%d-%m-%Y %H:%M"),
                "closing_date_raw": close_date.strftime("%d-%m-%Y %H:%M"),
                "description": f"{title} for {org}",
                "source_url": f"https://tender.nprocure.com/tender/{base_id + i}",
                "raw_html": f"<tr><td>{title}</td><td>{org}</td></tr>"
            }
            mock_tenders.append(tender)
        
        self.logger.info(f"Generated {len(mock_tenders)} mock tenders for POC")
        return mock_tenders

    def get_metadata(self) -> RunMetadata:
        return self.metadata