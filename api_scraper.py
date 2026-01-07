"""
API-based scraper for PSA Squash Tour rankings.

Fetches ranking data from the PSA backend API and parses it
into a clean, structured dataset using shared parsing utilities.
"""

import requests
import pandas as pd
from parser import parse_api_player

# PSA API endpoint for men's rankings
URL = "https://psa-api.ptsportsuite.com/rankedplayers/male"

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# Make request
response = requests.get(URL, headers=headers)
response.raise_for_status()

# Parse JSON response
raw_data = response.json()

# Use parser to extract required fields
players = []
for player in raw_data:
    players.append(parse_api_player(player))

# Convert to DataFrame
df = pd.DataFrame(players)

# Save output
df.to_csv("psa_rankings_api.csv", index=False)

print("Saved psa_rankings_api.csv")
print("Total players:", len(df))
print(df.head())