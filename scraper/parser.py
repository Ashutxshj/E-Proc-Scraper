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

        # Try multiple table selectors (the site might use different classes)
        table = (
            soup.find('table', class_='dataTable') or
            soup.find('table', class_='table') or
            soup.find('table')
        )
        
        if not table:
            self.logger.warning("No tender table found in HTML")
            # Fallback: try to find tender links directly
            return self._parse_from_links(soup)

        # Find all rows - skip header(s)
        all_rows = table.find_all('tr')
        self.logger.info(f"Found {len(all_rows)} total rows in table")
        
        # Skip first row if it's a header
        rows = all_rows[1:] if len(all_rows) > 1 else all_rows

        for idx, row in enumerate(rows):
            cols = row.find_all(['td', 'th'])  # Some sites use th in body
            
            if len(cols) < 3:  # Need at least title, org, type
                continue

            try:
                tender_data = self._extract_tender_from_row(row, cols)
                if tender_data:
                    tenders.append(tender_data)
                    self.logger.info(f"Parsed tender {idx+1}: {tender_data['tender_id']}")
            except Exception as e:
                self.logger.error(f"Error parsing row {idx}: {e}")

        if not tenders:
            self.logger.warning("No tenders parsed from table, trying alternative method")
            return self._parse_from_links(soup)

        self.logger.info(f"Successfully parsed {len(tenders)} tenders from HTML")
        return tenders

    def _parse_from_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Fallback: Parse tenders from any links containing /tender/
        """
        tenders = []
        tender_links = soup.find_all('a', href=re.compile(r'/tender/\d+'))
        
        self.logger.info(f"Found {len(tender_links)} tender links")
        
        for link in tender_links:
            try:
                href = link.get('href', '')
                tender_id_match = re.search(r'/tender/(\d+)', href)
                
                if not tender_id_match:
                    continue
                    
                tender_id = tender_id_match.group(1)
                title = link.get_text(strip=True)
                
                # Try to find parent row for more info
                parent_row = link.find_parent('tr')
                organization = ""
                tender_type = "Works"  # Default
                
                if parent_row:
                    cells = parent_row.find_all(['td', 'th'])
                    if len(cells) > 1:
                        organization = cells[1].get_text(strip=True)
                    if len(cells) > 2:
                        tender_type = cells[2].get_text(strip=True)
                
                tender_data = {
                    "tender_id": tender_id,
                    "title": title,
                    "organization": organization or "Unknown Organization",
                    "tender_type_raw": tender_type,
                    "publish_date_raw": "",
                    "closing_date_raw": "",
                    "source_url": f"https://tender.nprocure.com{href}",
                    "raw_html": str(link.parent) if link.parent else str(link)
                }
                
                tenders.append(tender_data)
                self.logger.info(f"Parsed tender from link: {tender_id}")
                
            except Exception as e:
                self.logger.error(f"Error parsing link: {e}")
        
        return tenders

    def _extract_tender_from_row(self, row, cols) -> Optional[Dict[str, Any]]:
        """Extract tender data from table row"""
        # Find link in first few columns
        link = None
        for col in cols[:3]:  # Check first 3 columns
            link = col.find('a', href=re.compile(r'/tender/'))
            if link:
                break
        
        if not link:
            return None

        title = link.get_text(strip=True)
        href = link.get('href', '')

        # Extract tender ID from URL
        tender_id_match = re.search(r'/tender/(\d+)', href)
        if not tender_id_match:
            return None
            
        tender_id = tender_id_match.group(1)

        return {
            "tender_id": tender_id,
            "title": title,
            "organization": cols[1].get_text(strip=True) if len(cols) > 1 else "",
            "tender_type_raw": cols[2].get_text(strip=True) if len(cols) > 2 else "Works",
            "publish_date_raw": cols[3].get_text(strip=True) if len(cols) > 3 else "",
            "closing_date_raw": cols[4].get_text(strip=True) if len(cols) > 4 else "",
            "source_url": f"https://tender.nprocure.com{href}",
            "raw_html": str(row)[:500]  # Limit size
        }

    def parse_tender_from_json(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse tenders from JSON API response
        """
        tenders = []
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