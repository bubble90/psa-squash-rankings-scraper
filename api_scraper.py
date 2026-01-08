"""
API-based scraper for PSA Squash Tour rankings.

Fetches ranking data directly from the PSA backend API.
Includes:
- User-Agent rotation (to avoid static fingerprints)
- Optional proxy support via environment variables
"""

import os
import random
import requests
import pandas as pd

from parser import parse_api_player
from exporter import export_to_csv

# --------------------------------------------------
# PSA API endpoint
# --------------------------------------------------
URL = "https://psa-api.ptsportsuite.com/rankedplayers/male"

# --------------------------------------------------
# User-Agent rotation
# --------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
]

headers = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "application/json",
}

# --------------------------------------------------
# Optional proxy support (OFF by default)
# --------------------------------------------------
# Enable by setting HTTP_PROXY or HTTPS_PROXY
# Example:
# export HTTPS_PROXY="http://127.0.0.1:8080"

PROXY_URL = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")

proxies = None
if PROXY_URL:
    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL,
    }

# --------------------------------------------------
# Make request
# --------------------------------------------------
response = requests.get(
    URL,
    headers=headers,
    proxies=proxies,
    timeout=10
)

response.raise_for_status()

# --------------------------------------------------
# Parse response
# --------------------------------------------------
raw_data = response.json()

players = []
for player in raw_data:
    players.append(parse_api_player(player))

df = pd.DataFrame(players)

# --------------------------------------------------
# Export output
# --------------------------------------------------
export_to_csv(df, "data/psa_rankings_api.csv")

print("Total players:", len(df))
print(df.head())
