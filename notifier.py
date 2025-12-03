"""
Notification system for sending alerts about new iPhone listings
"""
import logging
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationManager:
    """Manager for sending notifications about new listings"""
    
    def __init__(self, method='console', smtp_config=None):
        """
        Initialize notification manager
        
        Args:
            method: Notification method ('console' or 'email')
            smtp_config: Dictionary with SMTP configuration for email notifications
        """
        self.method = method
        self.smtp_config = smtp_config or {}
    
    def send_notification(self, listing, matching_criteria):
        """
        Send notification about a new listing
        
        Args:
            listing: Listing object
            matching_criteria: List of ClientCriteria objects that match the listing
        """
        if self.method == 'console':
            self._send_console_notification(listing, matching_criteria)
        elif self.method == 'email':
            self._send_email_notification(listing, matching_criteria)
        else:
            logger.warning(f"Unknown notification method: {self.method}")
    
    def _send_console_notification(self, listing, matching_criteria):
        """
        Send notification to console (for testing/demo)
        
        Args:
            listing: Listing object
            matching_criteria: List of ClientCriteria objects
        """
        print("\n" + "="*70)
        print("🔔 NEW IPHONE LISTING NOTIFICATION")
        print("="*70)
        print(f"Title: {listing.title}")
        print(f"Price: {listing.price} {listing.currency}")
        print(f"Location: {listing.location}")
        print(f"URL: {listing.url}")
        print(f"\nMatching {len(matching_criteria)} client(s):")
        for criteria in matching_criteria:
            print(f"  - {criteria.client_name}")
            if criteria.client_email:
                print(f"    Email: {criteria.client_email}")
        print("="*70 + "\n")
        logger.info(f"Console notification sent for listing {listing.olx_id}")
    
    def _send_email_notification(self, listing, matching_criteria):
        """
        Send email notification
        
        Args:
            listing: Listing object
            matching_criteria: List of ClientCriteria objects
        """
        if not self.smtp_config:
            logger.error("SMTP configuration not provided for email notifications")
            return
        
        for criteria in matching_criteria:
            if not criteria.client_email:
                logger.warning(f"No email address for client {criteria.client_name}")
                continue
            
            try:
                self._send_email(listing, criteria)
                logger.info(f"Email sent to {criteria.client_email} for listing {listing.olx_id}")
            except Exception as e:
                logger.error(f"Failed to send email to {criteria.client_email}: {str(e)}")
    
    def _send_email(self, listing, criteria):
        """
        Send individual email
        
        Args:
            listing: Listing object
            criteria: ClientCriteria object
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New iPhone Listing Match: {listing.title}"
        msg['From'] = self.smtp_config.get('username', 'olx-scraper@example.com')
        msg['To'] = criteria.client_email
        
        # Create email body (text version doesn't need escaping)
        text = f"""
Hello {criteria.client_name},

A new iPhone listing matching your criteria has been posted on OLX.pl:

Title: {listing.title}
Price: {listing.price} {listing.currency}
Location: {listing.location}
URL: {listing.url}

Your search criteria:
- Price range: {criteria.min_price or 'Any'} - {criteria.max_price or 'Any'} PLN
- Keywords: {criteria.keywords or 'Any'}
- Location: {criteria.location_filter or 'Any'}

Act fast before it's gone!

---
This is an automated notification from OLX iPhone Listing Scraper
"""
        
        # Escape HTML to prevent XSS
        escaped_client_name = html.escape(criteria.client_name)
        escaped_title = html.escape(listing.title)
        escaped_location = html.escape(listing.location or '')
        escaped_url = html.escape(listing.url)
        
        html_content = f"""
<html>
<body>
    <h2>Hello {escaped_client_name},</h2>
    <p>A new iPhone listing matching your criteria has been posted on OLX.pl:</p>
    
    <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
        <h3>{escaped_title}</h3>
        <p><strong>Price:</strong> {listing.price} {listing.currency}</p>
        <p><strong>Location:</strong> {escaped_location}</p>
        <p><a href="{escaped_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Listing</a></p>
    </div>
    
    <h4>Your search criteria:</h4>
    <ul>
        <li>Price range: {criteria.min_price or 'Any'} - {criteria.max_price or 'Any'} PLN</li>
        <li>Keywords: {criteria.keywords or 'Any'}</li>
        <li>Location: {criteria.location_filter or 'Any'}</li>
    </ul>
    
    <p><em>Act fast before it's gone!</em></p>
    
    <hr>
    <p style="font-size: 12px; color: #666;">This is an automated notification from OLX iPhone Listing Scraper</p>
</body>
</html>
"""
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
    
    def check_criteria_match(self, listing, criteria):
        """
        Check if a listing matches client criteria
        
        Args:
            listing: Listing object
            criteria: ClientCriteria object
            
        Returns:
            Boolean indicating if listing matches criteria
        """
        # Check price range
        if criteria.min_price and listing.price and listing.price < criteria.min_price:
            return False
        
        if criteria.max_price and listing.price and listing.price > criteria.max_price:
            return False
        
        # Check keywords
        if criteria.keywords:
            keywords = [k.strip().lower() for k in criteria.keywords.split(',')]
            title_lower = listing.title.lower()
            if not any(keyword in title_lower for keyword in keywords):
                return False
        
        # Check location
        if criteria.location_filter and listing.location:
            location_filter_lower = criteria.location_filter.lower()
            listing_location_lower = listing.location.lower()
            if location_filter_lower not in listing_location_lower:
                return False
        
        return True
    
    def process_new_listings(self, listings, client_criteria):
        """
        Process new listings and send notifications for matches
        
        Args:
            listings: List of Listing objects
            client_criteria: List of ClientCriteria objects
            
        Returns:
            Dictionary with notification statistics
        """
        stats = {
            'total_listings': len(listings),
            'notifications_sent': 0,
            'matches_found': 0
        }
        
        for listing in listings:
            matching_criteria = []
            
            for criteria in client_criteria:
                if self.check_criteria_match(listing, criteria):
                    matching_criteria.append(criteria)
            
            if matching_criteria:
                stats['matches_found'] += 1
                self.send_notification(listing, matching_criteria)
                stats['notifications_sent'] += len(matching_criteria)
        
        return stats
