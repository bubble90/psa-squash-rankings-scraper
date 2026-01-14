# PSA Squash Rankings Scraper

A robust Python-based web scraper for fetching professional squash player rankings from the PSA World Tour. Features API-first approach with HTML fallback, resumable pagination, checkpoint recovery, and comprehensive logging.

## Features

- **Dual Scraping Strategy**: Primary API scraper with automatic HTML fallback
- **Resumable Scraping**: Checkpoint system allows recovery from interruptions
- **Pagination**: Efficiently handles large datasets with configurable page sizes
- **User Agent Rotation**: Systematic rotation to avoid rate limiting
- **Proxy Support**: Configurable HTTP/HTTPS proxy via environment variables
- **Error Handling**: Graceful fallback and detailed error reporting
- **Extensive Test Coverage**: Unit tests with mocking

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/psa-squash-rankings-scraper.git
cd psa-squash-rankings-scraper
```

### 2. Create virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Scrape both male and female rankings
python run_scraper.py

# Scrape only male rankings
python run_scraper.py --gender male

# Scrape only female rankings
python run_scraper.py --gender female
```

### Advanced Options

```bash
# Custom page size
python run_scraper.py --gender male --page-size 50

# Limit number of pages
python run_scraper.py --gender male --max-pages 5

# Start fresh (ignore checkpoints)
python run_scraper.py --gender male --no-resume

# Enable debug logging
python run_scraper.py --gender male --log-level DEBUG
```

### Command-Line Arguments

| Argument | Options | Default | Description |
|----------|---------|---------|-------------|
| `--gender` | `male`, `female`, `both` | `both` | Gender to scrape |
| `--page-size` | integer | `100` | Results per page |
| `--max-pages` | integer | `None` | Maximum pages to fetch |
| `--no-resume` | flag | `False` | Ignore checkpoints |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | Logging verbosity |

## Project Structure

```
psa-squash-rankings-scraper/
├── api_scraper.py           # Main API scraper with pagination
├── html_scraper.py          # Fallback HTML scraper
├── data_parser.py           # Schema validation and parsing
├── exporter.py              # CSV export utilities
├── logger.py                # Centralized logging configuration
├── run_scraper.py           # Main entry point
├── validator.py             # Data validation tool
├── test_parser.py           # Parser unit tests
├── test_checkpoints.py      # Checkpoint system tests
├── test_api_scraper.py      # API scraper tests
├── test_html_scraper.py     # HTML scraper tests
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── checkpoints/             # Checkpoint files (auto-created)
└── logs/                    # Log files (auto-created)
```

## How It Works

### 1. API Scraping (Primary)

The scraper fetches data from the PSA backend API:

```python
from api_scraper import get_rankings

# Fetch male rankings
df = get_rankings(gender="male", page_size=100, resume=True)
```

**Features:**
- Pagination with automatic page detection
- Checkpoint system for resumable scraping
- Systematic user agent rotation
- Proxy support via environment variables

### 2. HTML Scraping (Fallback)

If the API fails, automatically falls back to HTML parsing:

```python
from html_scraper import scrape_rankings_html

# Fallback scraping
df = scrape_rankings_html()
```

### 3. Data Validation

Schema validation ensures data integrity:

```python
from data_parser import parse_api_player, validate_api_schema

# Validates required fields before parsing
player_data = parse_api_player(raw_player_data)
```

### 4. Checkpoint System

Scraping progress is automatically saved:

```
checkpoints/
├── male_checkpoint.json
└── female_checkpoint.json
```

If scraping is interrupted, simply re-run the script to resume from the last checkpoint.

## Output

### CSV Files

Successfully scraped data is exported to:
- `psa_rankings_male.csv`
- `psa_rankings_female.csv`
- `psa_rankings_male_fallback.csv` (if API fails)
- `psa_rankings_female_fallback.csv` (if API fails)

### CSV Format

| Column | Type | Description |
|--------|------|-------------|
| `rank` | int | World ranking position |
| `player` | string | Player name |
| `tournaments` | int | Number of tournaments played |
| `points` | int | Total ranking points |

### Log Files

Timestamped log files are created in the `logs/` directory:

```
logs/psa_scraper_20260112_143025.log
```

## Testing

### Run All Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest test_parser.py -v

# Run with coverage
pytest --cov=. --cov-report=html -v

# Run tests matching pattern
pytest -k "checkpoint" -v
```

### Test Coverage

The project includes tests covering:
- Data parser validation (3 tests)
- Checkpoint system (10 tests)
- API scraping (14 tests)
- HTML scraping (15 tests)
- Export functionality
- Error handling
- Edge cases

View coverage report:

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Configuration

### Environment Variables

```bash
# Set proxy (optional)
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8080"
```

### Logging Configuration

Modify `logger.py` to customize:
- Log file location
- Log format
- Console/file log levels

## Validation

Validate scraped data:

```bash
# Validate male rankings
python validator.py male

# Validate female rankings
python validator.py female

# Validate both
python validator.py both
```

The validator compares API and HTML scraper outputs and displays:
- Row counts
- Top 5 players
- Data consistency checks

## Troubleshooting

### Issue: "command not found: pytest"

**Solution:**

```bash
pip install -r requirements.txt
# or
python3 -m pytest test_parser.py -v
```

### Issue: API returns no data

**Solution:**
- Check internet connection
- Verify API endpoint is accessible
- Check logs for detailed error messages
- Scraper will automatically fall back to HTML

### Issue: Checkpoint corruption

**Solution:**

```bash
# Delete checkpoints and start fresh
rm -rf checkpoints/
python run_scraper.py --no-resume
```

### Issue: Rate limiting

**Solution:**
- Reduce page size: `--page-size 50`
- Add delays between requests (modify `api_scraper.py`)
- Use proxy: Set `HTTP_PROXY` environment variable

## Examples

### Example 1: Quick Test

```bash
# Scrape first 2 pages of male rankings
python run_scraper.py --gender male --max-pages 2 --log-level DEBUG
```

### Example 2: Resume Interrupted Scrape

```bash
# First run (interrupted at page 5)
python run_scraper.py --gender male

# Resume from checkpoint
python run_scraper.py --gender male
```

### Example 3: Using as a Module

```python
from api_scraper import get_rankings
from exporter import export_to_csv

# Fetch data
df = get_rankings(gender="female", page_size=50, max_pages=10)

# Custom processing
top_10 = df.head(10)
print(f"Top 10 female players:\n{top_10}")

# Export
export_to_csv(top_10, "top_10_female.csv")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
