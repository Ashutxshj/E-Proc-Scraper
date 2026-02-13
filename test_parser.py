import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Fetching tender.nprocure.com...")
response = requests.get("https://tender.nprocure.com", verify=False)
html = response.text

print(f"✓ Got HTML ({len(html)} chars)")
print()

soup = BeautifulSoup(html, 'lxml')

tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

datatable = soup.find('table', {'class': 'dataTable'})
if datatable:
    print("✓ Found DataTable!")
    rows = datatable.find_all('tr')
    print(f"  Table has {len(rows)} rows")
else:
    print("⚠️  No DataTable found")

tender_links = soup.find_all('a', href=lambda x: x and '/tender/' in x)
print(f"Found {len(tender_links)} tender links")

if tender_links:
    print("\nFirst 5 tender links:")
    for i, link in enumerate(tender_links[:5], 1):
        print(f"  {i}. {link.get_text(strip=True)[:60]}")
        print(f"     -> {link.get('href')}")
else:
    print("\n⚠️  No tender links found!")
    print("Checking if DataTable is empty...")
    
    if 'dataTable' in html or 'DataTable' in html:
        print("⚠️  Site uses DataTables (JavaScript-rendered content)")
        print("⚠️  The table is probably empty on initial load")
        
    if 'ng-app' in html or 'angular' in html.lower():
        print("⚠️  Site uses AngularJS (JavaScript-rendered)")
        
    tbody = soup.find('tbody')
    if tbody:
        print(f"Found tbody with {len(tbody.find_all('tr'))} rows")

print("\n" + "="*60)
print("DIAGNOSIS:")
if tender_links:
    print("✓ GOOD: Found tender links. Parser should work!")
else:
    print("✗ BAD: No tender links. Site needs JavaScript rendering.")
    print("  SOLUTION: Use Selenium or find the AJAX API endpoint")
print("="*60)