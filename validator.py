"""
Validator for PSA Squash rankings scrapers.

Compares HTML and API scraper outputs to validate completeness.
"""

import pandas as pd
from pandas.errors import EmptyDataError

HTML_FILE = "psa_rankings_html.csv"
API_FILE = "psa_rankings_api.csv"

# Load API data (this should always exist)
api_df = pd.read_csv(API_FILE)

# Try loading HTML data safely
try:
    html_df = pd.read_csv(HTML_FILE)
except EmptyDataError:
    html_df = pd.DataFrame()

print("HTML scraper rows:", len(html_df))
print("API scraper rows:", len(api_df))

if len(html_df) == 0:
    print("HTML scraper returned no data (expected due to JS-rendered content).")

if len(api_df) > 0:
    print("API scraper successfully returned ranking data.")

if len(html_df) > 0:
    if html_df.iloc[0]["player"] == api_df.iloc[0]["player"]:
        print("Top-ranked player matches between HTML and API.")
    else:
        print("Top-ranked player does NOT match.")
else:
    print("Skipping row-by-row comparison due to empty HTML dataset.")
