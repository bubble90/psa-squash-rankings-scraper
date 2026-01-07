"""
Exporter utilities for PSA Squash rankings project.

Handles exporting parsed ranking data to disk.
"""

def export_to_csv(df, filename):
    """
    Export a pandas DataFrame to a CSV file.

    Parameters:
    - df: pandas DataFrame containing ranking data
    - filename: output CSV file name
    """
    df.to_csv(filename, index=False)
    print(f"Exported data to {filename}")