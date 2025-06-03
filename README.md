# Brand24 Scraper

A Python-based web scraper for Brand24 using Selenium.

## Setup

1. Install Python 3.8 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root directory with your Brand24 credentials:
   ```
   BRAND24_EMAIL=your_email@example.com
   BRAND24_PASSWORD=your_password
   ```

## Usage

Run the scraper:
```bash
python brand24_scraper.py
```

## Features

- Automated login to Brand24
- Chrome WebDriver setup with appropriate options
- Error handling and graceful cleanup

## Note

Make sure you have Chrome browser installed on your system. The script uses ChromeDriver which will be automatically downloaded and managed by webdriver-manager. 