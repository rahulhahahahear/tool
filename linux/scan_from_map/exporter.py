"""
Exporter module for Google Maps Scraper
Exports data records to CSV and formatted TXT files.
"""

import csv
import datetime
from typing import List, Dict, Any


def export_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Exports business records to CSV format.
    Uses 'utf-8-sig' to ensure proper encoding when opened in Excel on Windows.
    """
    if not filepath.lower().endswith(".csv"):
        filepath += ".csv"

    fieldnames = [
        "Index",
        "Name",
        "Phone",
        "Website",
        "Rating",
        "Reviews",
        "Category",
        "Address",
        "Hours",
        "Google Maps URL",
        "Notes"
    ]

    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx, item in enumerate(data, 1):
            writer.writerow({
                "Index": idx,
                "Name": item.get("name", ""),
                "Phone": item.get("phone", ""),
                "Website": item.get("website", ""),
                "Rating": item.get("rating", ""),
                "Reviews": item.get("reviews", ""),
                "Category": item.get("category", ""),
                "Address": item.get("address", ""),
                "Hours": item.get("hours", ""),
                "Google Maps URL": item.get("url", ""),
                "Notes": item.get("notes", "")
            })


def export_to_txt(data: List[Dict[str, Any]], filepath: str, keyword: str = "") -> None:
    """
    Exports business records to a formatted human-readable TXT report.
    """
    if not filepath.lower().endswith(".txt"):
        filepath += ".txt"

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "=" * 80
    subdivider = "-" * 80

    with open(filepath, mode="w", encoding="utf-8") as txtfile:
        txtfile.write(f"{divider}\n")
        txtfile.write("GOOGLE MAPS SCRAPED DATA REPORT\n")
        if keyword:
            txtfile.write(f"Search Query: {keyword}\n")
        txtfile.write(f"Total Businesses: {len(data)}\n")
        txtfile.write(f"Export Timestamp: {now_str}\n")
        txtfile.write(f"{divider}\n\n")

        for idx, item in enumerate(data, 1):
            txtfile.write(f"[{idx}] {item.get('name', 'N/A')}\n")
            txtfile.write(f"{subdivider}\n")

            phone = item.get("phone") or "N/A"
            website = item.get("website") or "N/A"
            rating = item.get("rating") or "N/A"
            reviews = item.get("reviews")
            rating_str = f"{rating} ({reviews} reviews)" if reviews else rating
            category = item.get("category") or "N/A"
            address = item.get("address") or "N/A"
            hours = item.get("hours") or "N/A"
            url = item.get("url") or "N/A"
            notes = item.get("notes") or ""

            txtfile.write(f"  Phone:     {phone}\n")
            txtfile.write(f"  Website:   {website}\n")
            txtfile.write(f"  Rating:    {rating_str}\n")
            txtfile.write(f"  Category:  {category}\n")
            txtfile.write(f"  Address:   {address}\n")
            txtfile.write(f"  Hours:     {hours}\n")
            txtfile.write(f"  Maps URL:  {url}\n")
            if notes:
                txtfile.write(f"  Notes:     {notes}\n")
            txtfile.write("\n")

        txtfile.write(f"{divider}\n")
        txtfile.write("END OF REPORT\n")
        txtfile.write(f"{divider}\n")
