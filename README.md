PSA Squash Rankings Scraper

A robust and modular Python scraper for retrieving PSA Squash Tour rankings for both men and women.

This project is designed with robustness, reusability, and clarity in mind, addressing common real-world scraping concerns such as API changes, pagination assumptions, proxy usage, and maintainability.

FEATURES

- Supports men’s and women’s rankings
- Uses the PSA backend API rather than brittle HTML scraping
- User-Agent rotation to avoid static request fingerprints
- Optional proxy support via environment variables
- Defensive handling of future API pagination
- Schema validation to detect API changes early
- Fallback system (API → HTML scraper)
- Modular design (scraping logic reusable as an import)
- Unit tests for core parsing and fallback logic
- Clean CSV outputs

PROJECT STRUCTURE

psa-squash-rankings-scraper/
- api_scraper.py        Reusable API scraping logic
- html_scraper.py       HTML fallback scraper (limited)
- run_scraper.py        Entry point with fallback logic
- parser.py             Schema validation and normalization
- exporter.py           CSV export utilities
- validator.py          Dataset sanity checks
- requirements.txt
- README.md
- data/
  - psa_rankings_male.csv
  - psa_rankings_female.csv
- tests/
  - test_parser.py
  - test_fallback.py

INSTALLATION

Requirements:
- Python 3.9+
- pip

Install dependencies:
pip install -r requirements.txt

USAGE

Run the scraper:
python3 run_scraper.py

This will:
- Fetch men’s and women’s PSA rankings
- Save CSV files to the data/ directory

Output files:
- data/psa_rankings_male.csv
- data/psa_rankings_female.csv

USING THE SCRAPER PROGRAMMATICALLY

from api_scraper import get_rankings
df = get_rankings("female")
print(df.head())

PROXY SUPPORT (OPTIONAL)

export HTTPS_PROXY=http://127.0.0.1:8080
python3 run_scraper.py

Unset when finished:
unset HTTPS_PROXY

Proxy support is optional and disabled by default.

PAGINATION NOTES

The PSA rankings API currently returns the entire rankings dataset in a single response.
Pagination on the PSA website is handled client-side for display purposes only.
The scraper defensively supports paginated API responses if the schema changes in the future.

SCHEMA VALIDATION

The parser includes explicit schema validation to ensure required API fields are present.
If the backend response changes, the scraper fails fast rather than silently producing incorrect data.

FALLBACK SYSTEM

The scraper prioritizes the API as the primary data source.
If the API fails at any stage, the system automatically falls back to the HTML scraper.
If all data sources fail, the program exits with a clear error message.

TESTING

pytest

Tests cover:
- API schema parsing
- Failure on missing fields
- Fallback behavior when the API fails

LIMITATIONS

- The HTML scraper is provided only as a fallback and may return limited data due to JavaScript-rendered content.
- Live HTTP requests are not unit-tested by design.
