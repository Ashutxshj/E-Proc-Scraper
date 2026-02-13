"""
Deduplication logic for tenders
"""
from typing import List, Set
from models.tender import Tender


class TenderDeduplicator:
    """Handle tender deduplication based on tender_id"""

    def __init__(self):
        self.seen_ids: Set[str] = set()

    def is_duplicate(self, tender: Tender) -> bool:
        """Check if tender is a duplicate"""
        return tender.tender_id in self.seen_ids

    def mark_seen(self, tender: Tender):
        """Mark tender as seen"""
        self.seen_ids.add(tender.tender_id)

    def deduplicate(self, tenders: List[Tender]) -> List[Tender]:
        """
        Remove duplicates from a list of tenders
        
        Returns:
            List of unique tenders
        """
        unique = []
        for tender in tenders:
            if not self.is_duplicate(tender):
                unique.append(tender)
                self.mark_seen(tender)

        return unique

    def get_duplicate_count(self, tenders: List[Tender]) -> int:
        """Count duplicates in a list"""
        return len(tenders) - len(self.deduplicate(tenders.copy()))