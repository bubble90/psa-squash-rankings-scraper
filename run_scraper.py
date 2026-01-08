"""
Unified runner with fallback logic.

Attempts to fetch PSA rankings using the API scraper first.
Falls back to HTML scraper if the API is unavailable.
"""

import sys

def run_api():
    try:
        import api_scraper
        return True
    except Exception as e:
        print("API scraper failed:")
        print(e)
        return False

def run_html():
    try:
        import html_scraper
        return True
    except Exception as e:
        print("HTML scraper failed:")
        print(e)
        return False


if __name__ == "__main__":
    print("Running PSA rankings scraper...")

    api_success = run_api()

    if api_success:
        print("Successfully retrieved data via API.")
        sys.exit(0)

    print("Falling back to HTML scraper...")
    html_success = run_html()

    if html_success:
        print("Retrieved data via HTML scraper (limited).")
        sys.exit(0)

    raise RuntimeError(
        "All data sources failed. Unable to retrieve PSA rankings."
    )