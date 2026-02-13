"""
Parser for extracting tender data from HTML/JSON responses
"""
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from utils.logger import RunLogger


class Parser:
    """Extracts structured tender data from HTML and JSON"""

    def __init__(self, logger: RunLogger):
        self.logger = logger

    def parse_tender_list_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse tender list from HTML table
        
        Args:
            html: HTML content containing tender table
            
        Returns:
            List of raw tender dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        tenders = []

        # Look for tender rows in table
        table = soup.find('table', class_='dataTable')
        if not table:
            self.logger.warning("No tender table found in HTML")
            return tenders

        rows = table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            try:
                tender_data = self._extract_tender_from_row(row, cols)
                if tender_data:
                    tenders.append(tender_data)
            except Exception as e:
                self.logger.error(f"Error parsing row: {e}")

        self.logger.info(f"Parsed {len(tenders)} tenders from HTML")
        return tenders

    def _extract_tender_from_row(self, row, cols) -> Optional[Dict[str, Any]]:
        """Extract tender data from table row"""
        # Extract tender link and ID
        title_cell = cols[0] if len(cols) > 0 else None
        link = title_cell.find('a') if title_cell else None

        if not link:
            return None

        title = link.get_text(strip=True)
        href = link.get('href', '')

        # Extract tender ID from URL
        tender_id_match = re.search(r'/tender/(\d+)', href)
        tender_id = tender_id_match.group(1) if tender_id_match else "UNKNOWN"

        return {
            "tender_id": tender_id,
            "title": title,
            "organization": cols[1].get_text(strip=True) if len(cols) > 1 else "",
            "tender_type_raw": cols[2].get_text(strip=True) if len(cols) > 2 else "",
            "publish_date_raw": cols[3].get_text(strip=True) if len(cols) > 3 else "",
            "closing_date_raw": cols[4].get_text(strip=True) if len(cols) > 4 else "",
            "source_url": f"https://tender.nprocure.com{href}",
            "raw_html": str(row)
        }

    def parse_tender_from_json(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse tenders from JSON API response
        
        Args:
            json_data: JSON response from API
            
        Returns:
            List of raw tender dictionaries
        """
        tenders = []

        # The API response structure
        data_list = json_data.get('data', json_data) if isinstance(json_data, dict) else json_data

        if not isinstance(data_list, list):
            self.logger.warning(f"Unexpected JSON structure: {type(json_data)}")
            return tenders

        for item in data_list:
            try:
                tender_data = {
                    "tender_id": str(item.get('tenderId', item.get('id', 'UNKNOWN'))),
                    "title": item.get('title', item.get('tenderTitle', '')),
                    "organization": item.get('organization', item.get('organizationName', '')),
                    "tender_type_raw": item.get('tenderType', item.get('evaluationType', '')),
                    "publish_date_raw": item.get('publishDate', item.get('bidSubmissionStartDate', '')),
                    "closing_date_raw": item.get('closingDate', item.get('bidSubmissionEndDate', '')),
                    "description": item.get('description', item.get('tenderDescription', '')),
                    "source_url": f"https://tender.nprocure.com/tender/{item.get('tenderId', item.get('id', ''))}",
                    "attachments_raw": item.get('attachments', []),
                }
                tenders.append(tender_data)
            except Exception as e:
                self.logger.error(f"Error parsing JSON item: {e}")

        self.logger.info(f"Parsed {len(tenders)} tenders from JSON")
        return tenders