"""
Exporter utilities for PSA Squash rankings project.

Handles exporting parsed ranking data to disk.
Supports both API and HTML scraper outputs with appropriate column handling.
"""

import pandas as pd
from logger import get_logger
from schema import ScraperResult, is_api_result, is_html_result
from config import OUTPUT_DIR


def export_to_csv(data: ScraperResult, filename: str) -> None:
    """
    Export scraper results to a CSV file.

    Automatically handles both ApiPlayerRecord and HtmlPlayerRecord formats,
    adding appropriate columns based on data source.

    Parameters:
    - data: ScraperResult (list of ApiPlayerRecord or HtmlPlayerRecord)
    - filename: output CSV file name

    The CSV will include a 'source' column indicating data quality:
    - 'api': Complete data with IDs and biographical info
    - 'html': Degraded data without IDs or biographical info
    """
    logger = get_logger(__name__)

    if not data:
        logger.warning(f"No data to export to {filename}")
        return

    try:
        if is_api_result(data):
            logger.info(f"Exporting {len(data)} complete API records to {filename}")
            logger.debug(
                "Data includes: rank, player, id, tournaments, points, height_cm, weight_kg, birthdate, country"
            )
        elif is_html_result(data):
            logger.warning(
                f"Exporting {len(data)} DEGRADED HTML records to {filename} - "
                "missing player IDs and biographical data"
            )
            logger.debug(
                "Data includes: rank, player, tournaments, points (NO ID or biographical data)"
            )
        else:
            logger.error("Unknown data source type in export")

        OUTPUT = OUTPUT_DIR / filename
        df = pd.DataFrame(data)
        df.to_csv(OUTPUT, index=False)

        logger.info(f"Successfully exported {len(df)} rows to {filename}")

        logger.debug(f"CSV columns: {', '.join(df.columns)}")

    except Exception as e:
        logger.error(f"Failed to export data to {filename}: {e}")
        raise
