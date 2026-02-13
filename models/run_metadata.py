"""
Run metadata model for tracking scraper execution
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class RunMetadata:
    """
    Tracks metadata for each scraper run
    """
    run_id: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    scraper_version: str = "1.0.0"
    config: Dict[str, Any] = None
    tender_types_processed: List[str] = None
    pages_visited: int = 0
    tenders_parsed: int = 0
    tenders_saved: int = 0
    failures: int = 0
    deduped_count: int = 0
    error_summary: Dict[str, int] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.config is None:
            self.config = {}
        if self.tender_types_processed is None:
            self.tender_types_processed = []
        if self.error_summary is None:
            self.error_summary = {}

    @staticmethod
    def create_new(scraper_version: str, config: Dict[str, Any]):
        """Create a new run metadata instance"""
        return RunMetadata(
            run_id=str(uuid.uuid4()),
            start_time=datetime.utcnow().isoformat(),
            scraper_version=scraper_version,
            config=config
        )

    def finish(self):
        """Mark run as finished and calculate duration"""
        self.end_time = datetime.utcnow().isoformat()
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        self.duration_seconds = (end - start).total_seconds()

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)