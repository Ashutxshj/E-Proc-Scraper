import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from dateutil import parser as date_parser
from models.tender import Tender
from utils.logger import RunLogger


class Cleaner:

    def __init__(self, logger: RunLogger):
        self.logger = logger

    def clean_tender(self, raw_data: Dict[str, Any]) -> Optional[Tender]:
        try:
            return Tender(
                tender_id=self._clean_tender_id(raw_data.get('tender_id', '')),
                tender_type=self._normalize_tender_type(raw_data.get('tender_type_raw', '')),
                title=self._clean_text(raw_data.get('title', '')),
                organization=self._clean_text(raw_data.get('organization', '')),
                publish_date=self._normalize_date(raw_data.get('publish_date_raw', '')),
                closing_date=self._normalize_date(raw_data.get('closing_date_raw', ''), allow_null=True),
                description=self._clean_description(raw_data.get('description', raw_data.get('title', ''))),
                source_url=raw_data.get('source_url', ''),
                attachments=self._extract_attachments(raw_data.get('attachments_raw', [])),
                raw_html_snippet=raw_data.get('raw_html', '')[:500] if raw_data.get('raw_html') else None
            )
        except Exception as e:
            self.logger.error(f"Failed to clean tender: {e}")
            return None

    def _clean_tender_id(self, tender_id: str) -> str:
        cleaned = str(tender_id).strip()
        if not cleaned or cleaned == 'UNKNOWN':
            raise ValueError("Invalid tender ID")
        return cleaned

    def _normalize_tender_type(self, tender_type: str) -> str:
        tender_type = tender_type.upper().strip()

        if 'GOOD' in tender_type:
            return 'Goods'
        elif 'WORK' in tender_type:
            return 'Works'
        elif 'SERVICE' in tender_type or 'SERV' in tender_type:
            return 'Services'
        else:
            return 'Works'  # Default

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Trim
        text = text.strip()

        return text

    def _clean_description(self, description: str) -> str:
        desc = self._clean_text(description)

        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r'For more details.*',
            r'Please visit.*',
            r'Click here.*',
        ]

        for pattern in boilerplate_patterns:
            desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)

        return desc.strip()

    def _normalize_date(self, date_str: str, allow_null: bool = False) -> Optional[str]:
        if not date_str or date_str.strip() == '':
            if allow_null:
                return None
            else:
                return datetime.now().strftime('%Y-%m-%d')

        try:
            # Remove time component if present
            date_str = date_str.strip()
            date_str = re.sub(r'\s+\d{1,2}:\d{2}.*$', '', date_str)

            # Parse using dateutil
            parsed_date = date_parser.parse(date_str, dayfirst=True)
            return parsed_date.strftime('%Y-%m-%d')

        except Exception as e:
            self.logger.warning(f"Failed to parse date '{date_str}': {e}")
            if allow_null:
                return None
            else:
                return datetime.now().strftime('%Y-%m-%d')

    def _extract_attachments(self, attachments_raw: Any) -> List[str]:
        if not attachments_raw:
            return []

        if isinstance(attachments_raw, str):
            return [attachments_raw] if attachments_raw else []

        if isinstance(attachments_raw, list):
            return [str(att) for att in attachments_raw if att]

        return []