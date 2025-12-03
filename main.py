#!/usr/bin/env python3
"""
OLX iPhone Listings Scraper and Notifier

This application scrapes iPhone listings from OLX.pl, stores them in a database,
and sends notifications to clients when listings match their criteria.
"""
import os
import sys
import time
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv

from database import DatabaseManager
from scraper import OLXScraper
from notifier import NotificationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('olx_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class OLXMonitor:
    """Main application class for monitoring OLX listings"""
    
    def __init__(self):
        """Initialize the OLX monitor"""
        # Database setup
        self.db_url = os.getenv('DATABASE_URL', 'sqlite:///olx_listings.db')
        self.db_manager = DatabaseManager(self.db_url)
        logger.info(f"Database initialized: {self.db_url}")
        
        # Scraper setup
        self.olx_url = os.getenv('OLX_SEARCH_URL', 'https://www.olx.pl/d/elektronika/telefony/iphone/')
        self.scraper = OLXScraper(self.olx_url)
        logger.info(f"Scraper initialized for: {self.olx_url}")
        
        # Notification setup
        self.notification_method = os.getenv('NOTIFICATION_METHOD', 'console')
        smtp_config = None
        
        if self.notification_method == 'email':
            smtp_config = {
                'server': os.getenv('SMTP_SERVER'),
                'port': int(os.getenv('SMTP_PORT', 587)),
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD')
            }
        
        self.notifier = NotificationManager(self.notification_method, smtp_config)
        logger.info(f"Notification manager initialized: {self.notification_method}")
    
    def scrape_and_process(self):
        """Scrape listings and process new ones"""
        logger.info("Starting scraping job...")
        start_time = datetime.now()
        
        try:
            # Scrape listings
            listings_data = self.scraper.scrape_listings(max_pages=3)
            logger.info(f"Scraped {len(listings_data)} listings")
            
            # Add new listings to database
            new_listings = []
            for listing_data in listings_data:
                try:
                    listing = self.db_manager.add_listing(listing_data)
                    if listing:
                        new_listings.append(listing)
                except Exception as e:
                    logger.error(f"Error adding listing {listing_data.get('olx_id')}: {str(e)}")
            
            logger.info(f"Added {len(new_listings)} new listings to database")
            
            # Get active client criteria
            client_criteria = self.db_manager.get_active_criteria()
            logger.info(f"Found {len(client_criteria)} active client criteria")
            
            # Process notifications
            if new_listings and client_criteria:
                stats = self.notifier.process_new_listings(new_listings, client_criteria)
                logger.info(f"Notification stats: {stats}")
                
                # Mark notified listings
                for listing in new_listings:
                    self.db_manager.mark_as_notified(listing.id)
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Scraping job completed in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during scraping job: {str(e)}", exc_info=True)
    
    def add_sample_criteria(self):
        """Add sample client criteria for testing"""
        try:
            sample_criteria = {
                'client_name': 'John Doe',
                'client_email': 'john.doe@example.com',
                'min_price': 500.0,
                'max_price': 3000.0,
                'keywords': 'iPhone 12, iPhone 13, iPhone 14',
                'location_filter': 'Warszawa',
                'active': True
            }
            
            criteria_id, criteria_name = self.db_manager.add_client_criteria(sample_criteria)
            logger.info(f"Added sample criteria with ID: {criteria_id}")
            print(f"\n✅ Sample client criteria added for {sample_criteria['client_name']}")
            
        except Exception as e:
            logger.error(f"Error adding sample criteria: {str(e)}")
    
    def run_once(self):
        """Run scraping job once"""
        logger.info("Running single scraping job...")
        self.scrape_and_process()
    
    def run_scheduled(self, interval_minutes=30):
        """Run scraping job on a schedule"""
        logger.info(f"Starting scheduled scraping every {interval_minutes} minutes...")
        
        # Run immediately on start
        self.scrape_and_process()
        
        # Schedule periodic runs
        schedule.every(interval_minutes).minutes.do(self.scrape_and_process)
        
        print(f"\n🚀 OLX Monitor is running!")
        print(f"   Scraping every {interval_minutes} minutes")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping scheduled scraping...")
            print("\n👋 Goodbye!")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OLX iPhone Listings Scraper and Notifier')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--add-sample-criteria', action='store_true', help='Add sample client criteria')
    parser.add_argument('--interval', type=int, default=30, help='Scraping interval in minutes (default: 30)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = OLXMonitor()
    
    # Handle commands
    if args.add_sample_criteria:
        monitor.add_sample_criteria()
        return
    
    if args.once:
        monitor.run_once()
    else:
        # Get interval from environment or args
        interval = int(os.getenv('SCRAPE_INTERVAL_MINUTES', args.interval))
        monitor.run_scheduled(interval)


if __name__ == '__main__':
    main()
