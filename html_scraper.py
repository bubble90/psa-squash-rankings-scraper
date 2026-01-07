"""
HTML-based scraper for PSA Squash Tour rankings.

This script fetches the PSA rankings webpage, parses the rendered HTML
using BeautifulSoup, and extracts ranking data including rank, player name,
number of tournaments, and ranking points.

This method serves as a reliable baseline scraper and correctness reference
for comparison with the API-based scraping approach.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the PSA rankings page
URL = "https://www.psasquashtour.com/rankings/"

# Download the page
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

response = requests.get(URL, headers=headers)
response.raise_for_status()  # stops if the page didn't load

# Parse the HTML
soup = BeautifulSoup(response.text, "html.parser")

# Find the rankings table
table = soup.find("table")

if table is None:
    raise Exception("Could not find rankings table")

# Get all ranking rows
rows = table.find("tbody").find_all("tr")
print("Number of rows found:", len(rows))


data = []

for row in rows:
    cells = row.find_all("td")

    rank = int(cells[0].get_text(strip=True))
    player = cells[1].get_text(strip=True)
    tournaments = int(cells[2].get_text(strip=True))
    points = int(cells[3].get_text(strip=True).replace(",", ""))


    data.append({
        "rank": rank,
        "player": player,
        "tournaments": tournaments,
        "points": points
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv("psa_rankings_html.csv", index=False)

print("Saved psa_rankings_html.csv")