"""
Command Line Interface for Google Maps Scraper (scan_from_map module)
Allows running queries directly from PowerShell or Command Prompt.
"""

import argparse
import sys
import os

try:
    from .scraper import GoogleMapsScraper
    from .exporter import export_to_csv, export_to_txt
except (ImportError, ValueError):
    from scraper import GoogleMapsScraper
    from exporter import export_to_csv, export_to_txt


def main(custom_args=None):
    parser = argparse.ArgumentParser(
        prog="scan_from_map",
        description="Scrape Google Maps business listings (Name, Phone, Website, Address, Rating, etc.)"
    )
    parser.add_argument("keyword", nargs="?", type=str, help="Search keyword (e.g., 'dentist in new york')")
    parser.add_argument("-k", "--query", type=str, dest="query_opt", help="Alternative keyword parameter")
    parser.add_argument("-l", "--limit", type=int, default=15, help="Maximum results to scrape (default: 15)")
    parser.add_argument("--csv", type=str, help="Output CSV filepath")
    parser.add_argument("--txt", type=str, help="Output TXT filepath")
    parser.add_argument("--browser", choices=["chrome", "msedge"], default="chrome", help="Browser engine")
    parser.add_argument("--visible", action="store_true", help="Show browser window while scraping")

    args = parser.parse_args(custom_args)

    search_query = args.keyword or args.query_opt
    if not search_query:
        search_query = input("Enter search keyword for Google Maps: ").strip()

    if not search_query:
        print("Error: No keyword provided.")
        sys.exit(1)

    print(f"\n==========================================")
    print(f"  Google Maps Scraper - CLI Mode")
    print(f"  Keyword: {search_query}")
    print(f"  Limit:   {args.limit}")
    print(f"  Browser: {args.browser} (Headless: {not args.visible})")
    print(f"==========================================\n")

    def on_progress(msg):
        print(f"[*] {msg}")

    def on_item(item, current, total):
        print(f"    -> [{current}/{total}] {item['name']} | Phone: {item['phone']} | Web: {item['website']}")

    scraper = GoogleMapsScraper(
        headless=not args.visible,
        preferred_channel=args.browser,
        on_progress=on_progress,
        on_item_scraped=on_item
    )

    try:
        results = scraper.scrape(search_query, max_results=args.limit)
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        results = []

    print(f"\nExtracted {len(results)} records.\n")

    csv_file = args.csv
    txt_file = args.txt

    if not csv_file and not txt_file:
        sanitized = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in search_query).strip().replace(" ", "_")
        csv_file = f"{sanitized}_results.csv"
        txt_file = f"{sanitized}_results.txt"

    if csv_file:
        export_to_csv(results, csv_file)
        print(f"[+] Saved CSV to: {os.path.abspath(csv_file)}")

    if txt_file:
        export_to_txt(results, txt_file, keyword=search_query)
        print(f"[+] Saved TXT to: {os.path.abspath(txt_file)}")

    print("\nDone!")
    return results


if __name__ == "__main__":
    main()
