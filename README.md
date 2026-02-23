# PSA Squash Rankings Scraper

A robust Python-based web scraper for fetching professional squash player rankings from the PSA World Tour. Features **explicit typing** with distinct schemas for API and HTML fallback data, ensuring consumers are always aware when working with degraded data.

## Features

- **Explicit Fallback Typing**: Distinct `ApiPlayerRecord` and `HtmlPlayerRecord` types make data quality visible
- **Type-Safe Data Handling**: Type guards and union types prevent silent schema mismatches
- **API-First Approach**: Primary API scraper with automatic HTML fallback
- **Resumable Scraping**: Checkpoint system allows recovery from interruptions
- **Pagination**: Efficiently handles large datasets with configurable page sizes
- **User Agent Rotation**: Both scrapers use systematic rotation to avoid rate limiting
- **Proxy Support**: Configurable HTTP/HTTPS proxy via environment variables (both scrapers)
- **Comprehensive Logging**: Data quality warnings make degraded data explicit
- **Modern Tooling**: Uses uv for fast dependency management and ruff for linting

## Requirements

- Python 3.12+
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
    source: Literal["html"]      # ⚠ Degraded data indicator
    # ✗ NO player ID
    # ✗ NO biographical data
```

**Use for**: Display purposes only when API is unavailable

**Cannot be used for**: Joining datasets, player tracking, biographical analysis

## Usage

### Basic Usage

```bash
# Scrape both male and female rankings
uv run run_scraper.py

# Scrape only male rankings
uv run run_scraper.py --gender male

# Scrape only female rankings
uv run run_scraper.py --gender female
```

### Advanced Options

```bash
# Custom page size
uv run run_scraper.py --gender male --page-size 50

# Limit number of pages
uv run run_scraper.py --gender male --max-pages 5

# Start fresh (ignore checkpoints)
uv run run_scraper.py --gender male --no-resume

# Enable debug logging
uv run run_scraper.py --gender male --log-level DEBUG
```

### Programmatic Usage with Type Safety

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
│   ├── test_parser.py
│   ├── test_checkpoints.py
│   ├── test_exporter.py
│   └── test_schema.py
├── .github/
│   └── workflows/
│       └── CI.yml
├── pyproject.toml
├── README.md
├── LICENSE
├── uv.lock
└── .gitignore
```

## Output Files

### CSV Files

Successfully scraped data is exported to the output/ directory with clear naming:

- `output/psa_rankings_male.csv` - Male rankings (complete API data)
- `output/psa_rankings_female.csv` - Female rankings (complete API data)
- `output/psa_rankings_male_fallback.csv` - Male fallback (degraded HTML data)

### CSV Format

**API Data CSV** (complete):
```csv
rank,player,id,tournaments,points,height_cm,weight_kg,birthdate,country,source
1,Ali Farag,123,15,2500,180,75,1992-01-01,Egypt,api
```

**HTML Fallback CSV** (degraded):
```csv
rank,player,tournaments,points,source
1,Ali Farag,15,2500,html
```

Note the `source` column indicates data quality.

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