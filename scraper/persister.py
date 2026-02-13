"""
Persister for saving tender data and run metadata
"""
import json
import sqlite3
from typing import List
from pathlib import Path
from models.tender import Tender
from models.run_metadata import RunMetadata
from utils.logger import RunLogger
from utils.dedup import TenderDeduplicator


class Persister:
    """Handles saving tender data and run metadata"""

    def __init__(self, logger: RunLogger, output_path: str, metadata_db: str):
        self.logger = logger
        self.output_path = Path(output_path)
        self.metadata_db = Path(metadata_db)
        self.deduplicator = TenderDeduplicator()

        # Ensure directories exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_db.parent.mkdir(parents=True, exist_ok=True)

        # Initialize metadata database
        self._init_metadata_db()

    def _init_metadata_db(self):
        """Initialize SQLite database for run metadata"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs_metadata (
                run_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                duration_seconds REAL,
                scraper_version TEXT,
                config TEXT,
                tender_types_processed TEXT,
                pages_visited INTEGER,
                tenders_parsed INTEGER,
                tenders_saved INTEGER,
                failures INTEGER,
                deduped_count INTEGER,
                error_summary TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def save_tenders(self, tenders: List[Tender]) -> int:
        """
        Save tenders to JSON file with deduplication
        
        Returns:
            Number of tenders saved
        """
        if not tenders:
            self.logger.warning("No tenders to save")
            return 0

        # Load existing tenders if file exists
        existing_tenders = []
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for item in existing_data:
                        existing_tenders.append(Tender(**item))
                        self.deduplicator.mark_seen(Tender(**item))
            except Exception as e:
                self.logger.warning(f"Could not load existing tenders: {e}")

        # Deduplicate new tenders
        unique_tenders = self.deduplicator.deduplicate(tenders)
        all_tenders = existing_tenders + unique_tenders

        # Save to file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(
                [t.to_dict() for t in all_tenders],
                f,
                indent=2,
                ensure_ascii=False
            )

        self.logger.info(f"Saved {len(unique_tenders)} unique tenders (total: {len(all_tenders)})")
        return len(unique_tenders)

    def save_run_metadata(self, metadata: RunMetadata):
        """Save run metadata to SQLite database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO runs_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata.run_id,
            metadata.start_time,
            metadata.end_time,
            metadata.duration_seconds,
            metadata.scraper_version,
            json.dumps(metadata.config),
            json.dumps(metadata.tender_types_processed),
            metadata.pages_visited,
            metadata.tenders_parsed,
            metadata.tenders_saved,
            metadata.failures,
            metadata.deduped_count,
            json.dumps(metadata.error_summary)
        ))

        conn.commit()
        conn.close()

        self.logger.info(f"Saved run metadata for run_id: {metadata.run_id}")