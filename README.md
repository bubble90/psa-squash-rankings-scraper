# PSA Squash Rankings Scraper (Python)

## Overview

This project collects PSA Squash Tour player rankings using two complementary web scraping approaches:

1. HTML-based scraping using BeautifulSoup (baseline approach)
2. API-based scraping by reverse-engineering network requests used by the PSA website

The project demonstrates the trade-offs between traditional DOM scraping and modern API-driven data extraction, and highlights real-world challenges when scraping JavaScript-rendered websites.

## Project Structure

pspsa-squash-rankings-scraper/
├── scrapers/
│   ├── html_scraper.py
│   └── api_scraper.py
├── utils/
│   ├── parser.py
│   ├── exporter.py
│   └── validator.py
├── data/
│   ├── psa_rankings_api.csv
│   └── psa_rankings_html.csv
└── README.md

## Installation

Requirements:
- Python 3.9+
- pip

Install dependencies:

pip install requests beautifulsoup4 pandas

(On macOS, you may need python3 -m pip install ...)

## Usage

Run all commands from the project root directory.

Run the HTML scraper (baseline):

python3 scrapers/html_scraper.py

Expected behavior:
- Script runs successfully
- data/psa_rankings_html.csv is created
- The file is empty (0 rows)

Explanation:
The PSA rankings table is JavaScript-rendered, meaning the data is not present in the raw HTML returned by an HTTP request. This limitation is intentional and documented as part of the project.

Run the API scraper (primary data source):

python3 scrapers/api_scraper.py

Output:
- data/psa_rankings_api.csv
- ~900+ player rows
- Columns: rank, player, tournaments, points

Validate scraper outputs:

python3 utils/validator.py

Expected output:
- Confirms HTML scraper returned no data (expected)
- Confirms API scraper returned complete ranking data
- Skips row-by-row comparison due to empty HTML dataset

## Scraping Approaches Explained

HTML-Based Scraper:
- Uses requests and BeautifulSoup
- Attempts to extract rankings from the page DOM
- Fails due to JavaScript-rendered content

API-Based Scraper:
- Uses browser DevTools → Network → Fetch/XHR
- Identifies an undocumented PSA API endpoint
- Fetches structured JSON data directly
- Parses and normalizes required fields only

## Validation

The validator.py script confirms that HTML scraping fails for expected reasons and that API scraping returns complete and accurate ranking data.

## Key Takeaways

- Modern websites often do not expose data in HTML
- JavaScript-rendered content requires network-level inspection
- API scraping is more robust than DOM scraping
- Clean architecture improves maintainability and clarity
