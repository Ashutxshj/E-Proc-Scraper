from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class Tender:
    tender_id: str
    tender_type: str
    title: str
    organization: str
    publish_date: str 
    closing_date: Optional[str]  
    description: str
    source_url: str
    attachments: List[str]
    raw_html_snippet: Optional[str] = None
    ingested_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def __post_init__(self):
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow().isoformat()