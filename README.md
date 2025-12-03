# OLX iPhone Listings Scraper & Notifier

A Python application that monitors OLX.pl for new iPhone listings and sends notifications to clients when listings match their specified criteria.

## Features

- 🔍 **Web Scraping**: Automatically scrapes iPhone listings from OLX.pl
- 💾 **Database Storage**: Stores all listings in a SQLite database
- 🔔 **Smart Notifications**: Sends notifications when listings match client criteria
- 🎯 **Flexible Filtering**: Filter by price range, keywords, and location
- ⏰ **Scheduled Monitoring**: Runs on a configurable schedule
- 📧 **Multiple Notification Methods**: Console output or email notifications

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Permurez/fictional-spork.git
cd fictional-spork
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Configuration

The application is configured using environment variables in the `.env` file:

- `DATABASE_URL`: Database connection string (default: `sqlite:///olx_listings.db`)
- `SCRAPE_INTERVAL_MINUTES`: How often to scrape (default: 30 minutes)
- `OLX_SEARCH_URL`: OLX search URL (default: iPhone category)
- `NOTIFICATION_METHOD`: Notification type (`console` or `email`)

For email notifications, also configure:
- `SMTP_SERVER`: SMTP server address
- `SMTP_PORT`: SMTP port (default: 587)
- `SMTP_USERNAME`: Email username
- `SMTP_PASSWORD`: Email password

## Usage

### Add Client Criteria

First, add client notification criteria:

```bash
python main.py --add-sample-criteria
```

Or programmatically add criteria using the database manager.

### Run Once

To run a single scraping job:

```bash
python main.py --once
```

### Run Scheduled

To run continuous monitoring:

```bash
python main.py
```

Or with custom interval:

```bash
python main.py --interval 15  # Scrape every 15 minutes
```

## Project Structure

```
fictional-spork/
├── main.py              # Main application entry point
├── database.py          # Database models and manager
├── scraper.py           # OLX web scraper
├── notifier.py          # Notification system
├── requirements.txt     # Python dependencies
├── .env.example         # Example configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Client Criteria

Client criteria define what listings will trigger notifications. Each criteria includes:

- **Client Name**: Identifier for the client
- **Email**: Email address for notifications (if using email method)
- **Price Range**: Minimum and maximum price (in PLN)
- **Keywords**: Comma-separated keywords to match in listing titles
- **Location Filter**: Preferred location (e.g., "Warszawa", "Kraków")
- **Active**: Whether the criteria is active

## Database Schema

### Listings Table
Stores all scraped iPhone listings with fields like title, price, URL, location, etc.

### Client Criteria Table
Stores client notification preferences and filtering rules.

## Example Output

When a matching listing is found:

```
======================================================================
🔔 NEW IPHONE LISTING NOTIFICATION
======================================================================
Title: iPhone 13 Pro 128GB - Stan idealny
Price: 2500.0 PLN
Location: Warszawa
URL: https://www.olx.pl/d/oferta/...

Matching 1 client(s):
  - John Doe
    Email: john.doe@example.com
======================================================================
```

## Logging

The application logs all activities to:
- Console (stdout)
- `olx_scraper.log` file

## Troubleshooting

### No listings found
- Check the OLX_SEARCH_URL is correct
- OLX.pl may have changed their HTML structure
- Check your internet connection

### No notifications sent
- Ensure client criteria are added and active
- Verify criteria match some listings
- Check notification method is configured correctly

### Email not working
- Verify SMTP credentials are correct
- Check firewall/port settings
- Some email providers require app-specific passwords

## Contributing

This is a test project (Projekt testowy) for demonstration purposes.

## License

MIT License

## Author

Permurez
