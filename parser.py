"""
Shared parsing utilities for PSA scrapers.
"""

def parse_api_player(player):
    """
    Extract required fields from a PSA API player object.
    """
    return {
        "rank": player["World Ranking"],
        "player": player["Name"],
        "tournaments": int(player["Tournaments"]),
        "points": int(player["Total Points"])
    }
