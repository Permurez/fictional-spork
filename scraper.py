"""
Web scraper for OLX.pl iPhone listings
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OLXScraper:
    """Scraper for OLX.pl iPhone listings"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_listings(self, max_pages=3):
        """
        Scrape iPhone listings from OLX.pl
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of listing dictionaries
        """
        all_listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = self.base_url if page == 1 else f"{self.base_url}?page={page}"
                logger.info(f"Scraping page {page}: {url}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                listings = self._parse_page(response.text)
                all_listings.extend(listings)
                
                logger.info(f"Found {len(listings)} listings on page {page}")
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {str(e)}")
                break
        
        return all_listings
    
    def _parse_page(self, html):
        """
        Parse HTML page and extract listing information
        
        Args:
            html: HTML content of the page
            
        Returns:
            List of listing dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        listings = []
        
        # OLX uses different HTML structures, we'll try to find listings
        # Look for listing containers - OLX structure as of 2024
        listing_elements = soup.find_all('div', {'data-cy': 'l-card'})
        
        if not listing_elements:
            # Fallback: try alternative selectors
            listing_elements = soup.find_all('div', class_=re.compile(r'css-.*'))
        
        for element in listing_elements:
            try:
                listing = self._extract_listing_data(element)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"Error parsing listing element: {str(e)}")
                continue
        
        return listings
    
    def _extract_listing_data(self, element):
        """
        Extract listing data from a listing element
        
        Args:
            element: BeautifulSoup element containing listing data
            
        Returns:
            Dictionary with listing data or None
        """
        try:
            # Extract title
            title_elem = element.find('h6') or element.find('h4') or element.find('a', {'class': re.compile(r'.*title.*')})
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # Extract URL and OLX ID
            link_elem = element.find('a', href=True)
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://www.olx.pl' + url
            
            # Extract OLX ID from URL
            olx_id_match = re.search(r'ID([^\.]+)\.html', url)
            if not olx_id_match:
                # Try alternative pattern
                olx_id_match = re.search(r'-(\d+)\.html', url)
            
            if olx_id_match:
                olx_id = olx_id_match.group(1)
            else:
                # Use URL as ID if we can't extract it
                olx_id = url.split('/')[-1].replace('.html', '')
            
            # Extract price
            price = None
            price_elem = element.find('p', {'data-testid': 'ad-price'}) or element.find('span', class_=re.compile(r'.*price.*'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract numeric price
                price_match = re.search(r'([\d\s]+(?:,\d+)?)', price_text.replace(' ', ''))
                if price_match:
                    price_str = price_match.group(1).replace(',', '.').replace(' ', '')
                    try:
                        price = float(price_str)
                    except ValueError:
                        pass
            
            # Extract location
            location = None
            location_elem = element.find('p', {'data-testid': 'location-date'}) or element.find('span', class_=re.compile(r'.*location.*'))
            if location_elem:
                location = location_elem.get_text(strip=True)
                # Sometimes location is combined with date, try to split
                location_parts = location.split('-')
                if location_parts:
                    location = location_parts[0].strip()
            
            listing_data = {
                'olx_id': olx_id,
                'title': title,
                'price': price,
                'url': url,
                'location': location,
                'posted_date': datetime.utcnow(),
                'description': ''
            }
            
            return listing_data
            
        except Exception as e:
            logger.debug(f"Error extracting listing data: {str(e)}")
            return None
