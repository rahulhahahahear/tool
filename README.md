# 🛠️ Automation & Scraping Tool Hub

A modular, cross-platform desktop suite and command-line hub for automation, data scraping, and lead generation tasks on both **Windows** and **Linux**.

---

## 🗂️ Project Directory Structure

```
tool/
│
├── main.py                     # 🚀 Master Universal Launcher (Prompts: OS -> Mode -> Launch)
├── README.md                   # 📖 Full documentation and instructions
├── ai_rule.md                  # ⚠️ Mandatory rules for AI assistants
│
├── windows/                    # 🪟 Windows Platform Hub
│   ├── app.py                  # Windows Central Tool Hub GUI Dashboard
│   ├── cli.py                  # Windows Central Tool Hub CLI Dispatcher
│   ├── requirements.txt        # Windows dependencies
│   │
│   ├── scan_from_map/          # 📍 Tool 1: Google Maps Scraper (Windows Sandbox)
│   │   ├── scraper.py, exporter.py, app.py, cli.py, test_app.py, requirements.txt
│   │
│   └── yt_data_scraper/        # 🔴 Tool 2: YouTube Data Scraper (Windows Sandbox)
│       ├── scraper.py, exporter.py, app.py, cli.py, test_app.py, requirements.txt
│
└── linux/                      # 🐧 Linux Platform Hub
    ├── app.py                  # Linux Central Tool Hub GUI Dashboard
    ├── cli.py                  # Linux Central Tool Hub CLI Dispatcher
    ├── requirements.txt        # Linux dependencies
    │
    ├── scan_from_map/          # 📍 Tool 1: Google Maps Scraper (Linux Sandbox)
    │   ├── scraper.py, exporter.py, app.py, cli.py, test_app.py, requirements.txt
    │
    └── yt_data_scraper/        # 🔴 Tool 2: YouTube Data Scraper (Linux Sandbox)
        ├── scraper.py, exporter.py, app.py, cli.py, test_app.py, requirements.txt
```

---

## 🚀 How to Run

### Universal Master Launcher (Interactive)

Simply run:

```bash
python main.py
```

`main.py` will prompt you step-by-step:
1. **Select OS:** `[1] Windows` or `[2] Linux`
2. **Select Mode:** `[1] GUI`, `[2] CLI`, or `[3] Install Dependencies`

---

### Command-Line Direct Launch (Non-Interactive)

```bash
# Launch Windows GUI Dashboard
python main.py --os windows --mode gui

# List all available tools and dependency health
python main.py --os windows --mode cli list

# Run YouTube Data Scraper
python main.py --os windows --mode cli yt_data_scraper "tech reviews" --min-subscribers 10000 --limit 15

# Run Google Maps Scraper
python main.py --os windows --mode cli scan_from_map "coffee in brooklyn" --limit 10
```

---

## 🛠️ Available Tools

### 1. 📍 Scan From Map (`scan_from_map`)
* **Purpose**: Scrape Google Maps business listings by any keyword.
* **Fields**: Name, Phone, Website, Rating, Reviews, Category, Address, Hours, Maps URL, Notes.
* **Editing**: Real-time table filter, double-click editing modal, row addition & deletion.
* **Export**: **Custom Column Selection Dialog** on CSV & TXT export (choose exactly which columns to export).

### 2. 🔴 YouTube Data Scraper (`yt_data_scraper`)
* **Purpose**: Search YouTube by keyword to discover channels and video sources.
* **Fields**: Channel Name, Handle (`@...`), Subscribers (e.g. `1.5M`), Videos Count, Contact / Email, Website / Links, Discovered Video Title, Source Video URL, Channel URL, Bio/Description.
* **Filtering**:
  - Filter by **Subscriber Count** (e.g., Min Subscribers: `1,000`, `10,000`, `100,000`, etc.)
  - Real-time text filter (name, handle, email, website, video title)
* **Editing**: Double-click any channel to edit or add notes.
* **Export**: **Custom Column Selection Dialog** on CSV & TXT export (pick only the columns you want).

---

## 📦 How Dependencies are Handled Per Tool

Har tool ka apna alag `requirements.txt` hota hai uske sandbox folder me:
* Auto-detection when launching via GUI or CLI.
* Manual installation commands:
  ```bash
  # Specific tool
  python cli.py install yt_data_scraper
  python cli.py install scan_from_map

  # All tools at once
  python cli.py install all
  ```

---

## 🧪 Testing

Run all 14 automated unit tests across both platforms:

```bash
python -m unittest windows.scan_from_map.test_app linux.scan_from_map.test_app windows.yt_data_scraper.test_app linux.yt_data_scraper.test_app
```
