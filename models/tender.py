"""
Tender data model
"""
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class Tender:
    """
    Represents a tender entry with normalized fields
    """
    tender_id: str
    tender_type: str  # Goods | Works | Services
    title: str
    organization: str
    publish_date: str  # YYYY-MM-DD format
    closing_date: Optional[str]  # YYYY-MM-DD format or null
    description: str
    source_url: str
    attachments: List[str]
    raw_html_snippet: Optional[str] = None
    ingested_at: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

    def __post_init__(self):
        """Set ingestion timestamp"""
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow().isoformat()