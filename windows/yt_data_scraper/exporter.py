"""
Exporter module for YouTube Data Scraper
Exports data records to CSV and formatted TXT files with custom column selection support.
"""

import csv
import datetime
from typing import List, Dict, Any, Optional

ALL_COLUMNS = [
    ("Index", "Index"),
    ("Channel Name", "name"),
    ("Handle", "handle"),
    ("Subscribers", "subscribers"),
    ("Videos Count", "videos_count"),
    ("Contact / Email", "contact"),
    ("Website / Links", "website"),
    ("Source Video Title", "video_title"),
    ("Source Video URL", "video_url"),
    ("Channel URL", "channel_url"),
    ("Description", "description"),
]


def export_to_csv(
    data: List[Dict[str, Any]],
    filepath: str,
    selected_columns: Optional[List[str]] = None
) -> None:
    """
    Exports YouTube channel/video records to CSV format.
    Uses 'utf-8-sig' for seamless opening in Microsoft Excel and Google Sheets.
    """
    if not filepath.lower().endswith(".csv"):
        filepath += ".csv"

    active_cols = [
        (col_name, col_key) for col_name, col_key in ALL_COLUMNS
        if selected_columns is None or col_name in selected_columns
    ]
    if not active_cols:
        active_cols = ALL_COLUMNS

    fieldnames = [col_name for col_name, _ in active_cols]

    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx, item in enumerate(data, 1):
            row = {}
            for col_name, col_key in active_cols:
                if col_key == "Index":
                    row[col_name] = idx
                else:
                    row[col_name] = item.get(col_key, "")
            writer.writerow(row)


def export_to_txt(
    data: List[Dict[str, Any]],
    filepath: str,
    keyword: str = "",
    selected_columns: Optional[List[str]] = None
) -> None:
    """
    Exports YouTube records to a formatted human-readable TXT report.
    """
    if not filepath.lower().endswith(".txt"):
        filepath += ".txt"

    active_cols = [
        (col_name, col_key) for col_name, col_key in ALL_COLUMNS
        if (selected_columns is None or col_name in selected_columns) and col_name not in ("Index", "Channel Name")
    ]

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "=" * 80
    subdivider = "-" * 80

    with open(filepath, mode="w", encoding="utf-8") as txtfile:
        txtfile.write(f"{divider}\n")
        txtfile.write("YOUTUBE DATA SCRAPER REPORT\n")
        if keyword:
            txtfile.write(f"Search Query:      {keyword}\n")
        txtfile.write(f"Total Listings:    {len(data)}\n")
        txtfile.write(f"Export Timestamp:  {now_str}\n")
        txtfile.write(f"{divider}\n\n")

        for idx, item in enumerate(data, 1):
            name_val = item.get("name") or "N/A"
            txtfile.write(f"[{idx}] {name_val}\n")
            txtfile.write(f"{subdivider}\n")

            for col_name, col_key in active_cols:
                val = item.get(col_key) or "N/A"
                txtfile.write(f"  {col_name:20}: {val}\n")

            txtfile.write("\n")

        txtfile.write(f"{divider}\n")
        txtfile.write("END OF REPORT\n")
        txtfile.write(f"{divider}\n")
