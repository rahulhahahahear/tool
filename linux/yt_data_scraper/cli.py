"""
Command Line Interface for YouTube Data Scraper
Allows searching and scraping YouTube channels and video sources directly from terminal.
"""

import argparse
import sys
import os

try:
    from .scraper import YouTubeDataScraper, parse_subscribers_to_number
    from .exporter import export_to_csv, export_to_txt
except (ImportError, ValueError):
    from scraper import YouTubeDataScraper, parse_subscribers_to_number
    from exporter import export_to_csv, export_to_txt


def main(custom_args=None):
    parser = argparse.ArgumentParser(
        prog="yt_data_scraper",
        description="Scrape YouTube channels & videos (Name, Subscribers, Handle, Contact/Email, Website, Source Video, etc.)"
    )
    parser.add_argument("keyword", nargs="?", type=str, help="Search keyword (e.g. 'tech reviews', 'python')")
    parser.add_argument("-k", "--query", type=str, dest="query_opt", help="Alternative keyword parameter")
    parser.add_argument("-l", "--limit", type=int, default=15, help="Maximum results to scrape (default: 15)")
    parser.add_argument("-m", "--mode", choices=["both", "channels", "videos"], default="both", help="Search mode")
    parser.add_argument("--min-subscribers", type=int, default=0, help="Minimum subscribers filter (e.g. 10000)")
    parser.add_argument("--max-subscribers", type=int, default=0, help="Maximum subscribers filter")
    parser.add_argument("--csv", type=str, help="Output CSV filepath")
    parser.add_argument("--txt", type=str, help="Output TXT filepath")
    parser.add_argument("--browser", choices=["chrome", "msedge", "chromium"], default="chrome", help="Browser engine")
    parser.add_argument("--visible", action="store_true", help="Show browser window while scraping")
    parser.add_argument("--no-deep", action="store_true", help="Skip visiting channel About pages for faster scrape")

    args = parser.parse_args(custom_args)

    search_query = args.keyword or args.query_opt
    if not search_query:
        search_query = input("Enter search keyword for YouTube: ").strip()

    if not search_query:
        print("Error: No keyword provided.")
        sys.exit(1)

    print(f"\n==========================================")
    print(f"  YouTube Data Scraper - CLI Mode")
    print(f"  Keyword:         {search_query}")
    print(f"  Mode:            {args.mode.upper()}")
    print(f"  Limit:           {args.limit}")
    print(f"  Min Subscribers: {args.min_subscribers or 'None'}")
    print(f"  Browser:         {args.browser} (Headless: {not args.visible})")
    print(f"==========================================\n")

    def on_progress(msg):
        print(f"[*] {msg}")

    def on_item(item, current, total):
        print(f"    -> [{current}/{total}] {item['name']} ({item['subscribers']}) | Handle: {item['handle']} | Contact: {item['contact'] or 'None'} | Web: {item['website'] or 'None'}")

    scraper = YouTubeDataScraper(
        headless=not args.visible,
        preferred_channel=args.browser,
        fetch_channel_details=not args.no_deep,
        on_progress=on_progress,
        on_item_scraped=on_item
    )

    try:
        results = scraper.scrape(
            keyword=search_query,
            max_results=args.limit,
            search_mode=args.mode,
            min_subscribers=args.min_subscribers,
            max_subscribers=args.max_subscribers
        )
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        results = []

    print(f"\nExtracted {len(results)} records.\n")

    csv_file = args.csv
    txt_file = args.txt

    if not csv_file and not txt_file:
        sanitized = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in search_query).strip().replace(" ", "_")
        csv_file = f"youtube_{sanitized}_results.csv"
        txt_file = f"youtube_{sanitized}_results.txt"

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
