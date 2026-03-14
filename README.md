# PSA Squash Rankings Scraper

A robust Python-based web scraper for fetching professional squash player rankings from the PSA World Tour, as well as tournament listings and match results from squashinfo.com. Features **explicit typing** with distinct schemas for API and HTML fallback data, ensuring consumers are always aware when working with degraded data.

## Features

- **Explicit Fallback Typing**: Distinct `ApiPlayerRecord` and `HtmlPlayerRecord` types make data quality visible
- **Type-Safe Data Handling**: Type guards and union types prevent silent schema mismatches
- **API-First Approach**: Primary API scraper with automatic HTML fallback
- **Tournament Scraping**: Fetch recent PSA tournament listings from squashinfo.com
- **Match Result Scraping**: Fetch full draw and match results for any tournament event
- **Resumable Scraping**: Checkpoint system allows recovery from interruptions
- **Pagination**: Efficiently handles large datasets with configurable page sizes
- **User Agent Rotation**: Both scrapers use systematic rotation to avoid rate limiting
- **Proxy Support**: Configurable HTTP/HTTPS proxy via environment variables (both scrapers)
- **Comprehensive Logging**: Data quality warnings make degraded data explicit
- **Modern Tooling**: Uses uv for fast dependency management and ruff for linting

## Requirements

- Python 3.9+
- uv

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/psa-squash-rankings-scraper.git
cd psa-squash-rankings-scraper
```

### 2. Install dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev
```

## Data Quality: API vs HTML Fallback

This scraper uses **explicit typing** to make data quality visible to consumers.

### ApiPlayerRecord (Complete Data)

```python
class ApiPlayerRecord(TypedDict):
    rank: int
    player: str
    id: int                      # ✓ Unique player identifier
    tournaments: int
    points: int
    height_cm: Optional[int]     # ✓ Biographical data
    weight_kg: Optional[int]     # ✓ Biographical data
    birthdate: Optional[str]     # ✓ Biographical data
    country: Optional[str]       # ✓ Biographical data
    picture_url: Optional[str]   # ✓ Full player photo URL
    mugshot_url: Optional[str]   # ✓ Headshot photo URL
    source: Literal["api"]       # ✓ Data quality indicator
```

**Use for**: Production systems, data analysis, player tracking, joining datasets

### HtmlPlayerRecord (Degraded Fallback)

```python
class HtmlPlayerRecord(TypedDict):
    rank: int
    player: str
    tournaments: int
    points: int
    mugshot_url: Optional[str]   # ✓ Headshot photo URL (if present in HTML)
    source: Literal["html"]      # ⚠ Degraded data indicator
    # ✗ NO player ID
    # ✗ NO biographical data
```

**Use for**: Display purposes only when API is unavailable

**Cannot be used for**: Joining datasets, player tracking, biographical analysis

### TournamentRecord (squashinfo.com)

```python
class TournamentRecord(TypedDict):
    id: int                          # Numeric event ID
    name: str                        # Tournament name
    gender: Optional[str]            # "M", "W", or None
    tier: str                        # e.g. "PSA Platinum"
    location: str
    date: str
    url: str                         # Full squashinfo.com event URL
    source: Literal["squashinfo"]
```

### MatchRecord (squashinfo.com)

```python
class MatchRecord(TypedDict):
    match_id: int
    tournament_id: int
    tournament_name: str
    round: str                       # e.g. "Semi-finals", "Final"
    player1_name: str
    player1_id: Optional[int]
    player1_country: Optional[str]   # 3-letter country code
    player1_seeding: Optional[str]
    player2_name: str
    player2_id: Optional[int]
    player2_country: Optional[str]
    player2_seeding: Optional[str]
    winner: Optional[str]            # player1_name if completed, None if upcoming
    scores: Optional[str]            # e.g. "11-5, 11-4, 11-5"
    duration_minutes: Optional[int]
    source: Literal["squashinfo"]
```

## Usage

The CLI uses subcommands: `rankings`, `tournaments`, and `matches`.

### Rankings

```bash
# Scrape both male and female rankings (default)
psa-scrape rankings --gender both

# Scrape only top 100 male players with debug logging
psa-scrape rankings --gender male --page-size 100 --max-pages 1 --log-level DEBUG

# Disable checkpointing (start fresh)
psa-scrape rankings --gender male --no-resume
```

### Tournaments

Fetch recent PSA tournament listings from squashinfo.com (~20 tournaments per page).

```bash
# Fetch the most recent ~20 tournaments (default: 1 page)
psa-scrape tournaments

# Fetch more history (e.g. 5 pages ≈ 100 tournaments)
psa-scrape tournaments --max-pages 5
```

Output: `output/squashinfo_tournaments.csv`

### Matches

Fetch the full draw and match results for a specific tournament. You need the event ID and URL slug, both of which appear in the tournament listing output.

```bash
# Fetch matches for a tournament by event ID and slug
psa-scrape matches --event-id 11593 --slug mens-australian-open-2026
```

Output: `output/squashinfo_matches_11593.csv`

Upcoming matches are included with `winner=None` and `scores=None`. Completed matches include scores (e.g. `11-5, 11-4, 11-5`) and duration in minutes.

### Programmatic Usage — Tournaments & Matches

```python
from psa_squash_rankings.squashinfo_scraper import get_recent_tournaments, get_tournament_matches

# Fetch recent tournaments (last ~20)
tournaments = get_recent_tournaments(max_pages=1)
for t in tournaments:
    print(f"{t['date']}  [{t['tier']}]  {t['name']} ({t['gender']})  — {t['location']}")

# Fetch match results for a specific event
matches = get_tournament_matches(event_id=11593, slug="mens-australian-open-2026")
for m in matches:
    result = f"{m['winner']} bt opponent" if m['winner'] else "upcoming"
    print(f"{m['round']:20s}  {m['player1_name']} vs {m['player2_name']}  {result}")
```

### Programmatic Usage — Rankings (Type Safety)

```python
from api_scraper import get_rankings
from html_scraper import scrape_rankings_html
from schema import is_api_result, is_html_result, ScraperResult

# Try API first
try:
    result: ScraperResult = get_rankings("male")

    # Type-safe handling
    if is_api_result(result):
        # Safe to access 'id' field and biographical data
        for player in result:
            print(f"ID: {player['id']}, Name: {player['player']}")
            if player['country']:
                print(f"  Country: {player['country']}")

except Exception as e:
    print(f"API failed: {e}")

    # Explicit fallback with degraded data
    result = scrape_rankings_html()

    if is_html_result(result):
        # Code is aware this is degraded data
        print("WARNING: Using fallback data without IDs")
        for player in result:
            # Cannot access 'id' field - type checker will warn
            print(f"Name: {player['player']}, Rank: {player['rank']}")
```

## Project Structure

```
psa-squash-rankings/
├── src/
│   └── psa_squash_rankings/
│       ├── __init__.py
│       ├── py.typed
│       ├── api_scraper.py
│       ├── html_scraper.py
│       ├── squashinfo_scraper.py
│       ├── data_parser.py
│       ├── schema.py
│       ├── config.py
│       ├── logger.py
│       ├── exporter.py
│       ├── validator.py
│       └── cli.py
├── tests/
│   ├── conftest.py
│   ├── test_api_scraper.py
│   ├── test_html_scraper.py
│   ├── test_squashinfo_scraper.py
│   ├── test_parser.py
│   ├── test_checkpoints.py
│   ├── test_exporter.py
│   └── test_schema.py
├── .github/
│   └── workflows/
│       └── CI.yml
│       └── publish.yml
├── pyproject.toml
├── README.md
├── LICENSE
├── uv.lock
└── .gitignore
```

## Output Files

### CSV Files

Successfully scraped data is exported to the `output/` directory with clear naming:

**Rankings:**
- `output/psa_rankings_male.csv` — Male rankings (complete API data)
- `output/psa_rankings_female.csv` — Female rankings (complete API data)
- `output/psa_rankings_male_fallback.csv` — Male fallback (degraded HTML data)

**squashinfo.com:**
- `output/squashinfo_tournaments.csv` — Recent tournament listings
- `output/squashinfo_matches_{event_id}.csv` — Match results for a tournament

### CSV Format

**API Data CSV** (complete):
```csv
rank,player,id,tournaments,points,height_cm,weight_kg,birthdate,country,picture_url,mugshot_url,source
1,Ali Farag,123,15,2500,180,75,1992-01-01,Egypt,https://...players/123.jpg,https://...,api
```

**HTML Fallback CSV** (degraded):
```csv
rank,player,tournaments,points,mugshot_url,source
1,Ali Farag,15,2500,https://...,html
```

**Tournament CSV:**
```csv
id,name,gender,tier,location,date,url,source
11593,Mens Australian Open 2026,M,PSA Platinum,Sydney,Jan 2026,https://squashinfo.com/events/11593-...,squashinfo
```

**Matches CSV:**
```csv
match_id,tournament_id,tournament_name,round,player1_name,player1_id,player1_country,player1_seeding,player2_name,player2_id,player2_country,player2_seeding,winner,scores,duration_minutes,source
98765,11593,Mens Australian Open 2026,Final,Ali Farag,42,EGY,1,Paul Coll,57,NZL,2,Ali Farag,"11-5, 11-4, 11-5",42,squashinfo
```

The `source` column indicates the data origin (`api`, `html`, or `squashinfo`).

## How It Works

### 1. Explicit Type System

The scraper uses Python's `TypedDict` to define distinct schemas:

```python
# schema.py defines two incompatible types
ApiPlayerRecord   # Complete data with 'id' field
HtmlPlayerRecord  # Degraded data without 'id' field

# Type guards make checking explicit
if is_api_result(data):
    # Safe to use player['id']
elif is_html_result(data):
    # Cannot use player['id'] - not in schema
```

### 2. Fallback with Warnings

The scraper makes degraded data explicit through logging:

```
INFO: Attempting API scrape for male rankings...
ERROR: API scrape failed: Connection timeout
WARNING: ============================================================
WARNING: FALLING BACK TO HTML SCRAPER
WARNING: WARNING: HTML data is DEGRADED - missing player IDs and biographical info
WARNING: ============================================================
WARNING: Using HTML fallback scraper - data will be incomplete
```

### 3. Type-Safe Export

The exporter detects data quality and logs appropriately:

```python
if is_api_result(data):
    logger.info("Exporting complete API records")
elif is_html_result(data):
    logger.warning("Exporting DEGRADED HTML records - missing IDs")
```

## Validation

Validate scraped data with type-aware checks:

```bash
# Validate male rankings
uv validator.py male

# Validate female rankings
uv validator.py female

# Validate both
uv validator.py both
```

The validator displays:
- Data source (API vs HTML)
- Data quality assessment
- Schema completeness
- Available fields
- Recommendations for production use

Example output:
```
Data Quality Assessment:
--------------------------------------------------
API scraper results (500 players):
  ✓ Data source: API (COMPLETE DATA)
  ✓ Contains player IDs: Yes
  ✓ Contains biographical data: Yes
  ✓ Schema complete

Validation Summary:
--------------------------------------------------
✓ COMPLETE API DATA AVAILABLE - recommended for production use
```

## Development

### Code Quality

This project uses Ruff for linting and formatting:

```bash
# Check code
uv run ruff check .

# Format code
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Type Checking

```bash
# Install ty
uv pip install ty

# Run type checking
uv run ty check
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Configuration

### Environment Variables

```bash
# Set proxy (both API and HTML scrapers support this)
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8080"
```

### Logging Configuration

Modify `logger.py` to customize:
- Log file location
- Log format
- Console/file log levels

## Key Improvements Over Original

### 1. Explicit Typing
- **Before**: Silent schema mismatches between scrapers
- **After**: Distinct types (`ApiPlayerRecord` vs `HtmlPlayerRecord`) make data quality explicit

### 2. Consistent Network Behavior
- **Before**: Only API scraper supported proxies and UA rotation
- **After**: Both scrapers support proxies and UA rotation

### 3. Type-Safe Code
- **Before**: Consumers didn't know when they got degraded data
- **After**: Type guards (`is_api_result()`, `is_html_result()`) make checks explicit

### 4. Clear Warnings
- **Before**: Fallback happened silently
- **After**: Extensive logging warns about degraded data quality

### 5. Proper Resource Management
- **Before**: HTML scraper didn't close sessions
- **After**: Both scrapers use proper session cleanup

## Troubleshooting

### Issue: "command not found: uv"

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Issue: Type errors in IDE

**Solution:**
Make sure your IDE is using Python 3.12+ and has type checking enabled. The explicit typing requires modern Python.

### Issue: Fallback always used

**Solution:**
Check logs for API error details:
```bash
uv run run_scraper.py --log-level DEBUG
```

Common causes:
- Network connectivity issues
- Proxy misconfiguration
- API endpoint changes
- Rate limiting

### Issue: Missing player IDs in output

**Solution:**
Check the `source` column in your CSV:
- `source=api`: Should have IDs
- `source=html`: Expected - HTML data doesn't include IDs

If `source=html`, the scraper fell back to degraded data. Check logs to see why API failed.

## Examples

### Example 1: Type-Safe Data Processing

```python
from api_scraper import get_rankings
from schema import is_api_result
import pandas as pd

# Fetch data
result = get_rankings("male", max_pages=5)

# Type-safe processing
if is_api_result(result):
    # We know we have complete data with IDs
    df = pd.DataFrame(result)

    # Safe to use 'id' column for joins
    print(f"Player IDs available: {df['id'].notna().sum()}")

    # Safe to analyze biographical data
    print(f"Average height: {df['height_cm'].mean():.1f} cm")
else:
    print("WARNING: Degraded data - cannot perform ID-based analysis")
```

### Example 2: Handling Fallback Explicitly

```python
from run_scraper import scrape_gender
from schema import is_html_result

# Scrape with explicit fallback handling
data, is_fallback = scrape_gender("male", page_size=100, max_pages=None, resume=True)

if is_fallback:
    print("⚠ Using degraded HTML data")
    print("⚠ Cannot track players across time (no IDs)")
    print("⚠ Use for display purposes only")
else:
    print("✓ Complete API data available")
    print("✓ Safe for production use")
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Install dev dependencies (`uv sync --group dev`)
4. Make your changes and add tests
5. Ensure type safety: `uv run ty check`
6. Run tests: `uv run pytest`
7. Check code quality: `uv run ruff check .`
8. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
9. Push to the branch (`git push origin feature/AmazingFeature`)
10. Open a Pull Request

## Acknowledgments

- PSA World Tour for providing the ranking data

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.