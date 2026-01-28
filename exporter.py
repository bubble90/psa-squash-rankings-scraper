"""
Exporter utilities for PSA Squash rankings project.

Handles exporting parsed ranking data to disk.
"""

from logger import get_logger
from config import OUTPUT_DIR

logger = get_logger(__name__)


def export_to_csv(df, filename):
    """
    Export a pandas DataFrame to a CSV file.

    Parameters:
    - df: pandas DataFrame containing ranking data
    - filename: output CSV file name
    """
    try:
        OUTPUT = OUTPUT_DIR / filename
        df.to_csv(OUTPUT, index=False)
        logger.info(f"Exported {len(df)} rows to {filename}")
    except Exception as e:
        logger.error(f"Failed to export data to {filename}: {e}")
        raise
