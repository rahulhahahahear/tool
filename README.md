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
│   └── scan_from_map/          # 📍 Tool 1: Google Maps Scraper (Windows Sandbox)
│       ├── __init__.py
│       ├── scraper.py
│       ├── exporter.py
│       ├── app.py
│       ├── cli.py
│       ├── test_app.py
│       └── requirements.txt
│
└── linux/                      # 🐧 Linux Platform Hub
    ├── app.py                  # Linux Central Tool Hub GUI Dashboard
    ├── cli.py                  # Linux Central Tool Hub CLI Dispatcher
    ├── requirements.txt        # Linux dependencies
    └── scan_from_map/          # 📍 Tool 1: Google Maps Scraper (Linux Sandbox)
        ├── __init__.py
        ├── scraper.py
        ├── exporter.py
        ├── app.py
        ├── cli.py
        ├── test_app.py
        └── requirements.txt
```

---

## 🚀 How to Run

### Universal Master Launcher (Interactive)

Simply run:

```bash
python main.py
```

`main.py` will prompt you step-by-step:

```text
==================================================================
      🛠️  AUTOMATION & SCRAPING TOOL HUB - MASTER LAUNCHER
==================================================================

[?] Step 1: Select Operating System Platform:
  [1] Windows (Current Host) (Default)
  [2] Linux
Enter choice (1-2) [Default: 1]: 1

[?] Step 2: Select Interface Mode:
  [1] GUI (Desktop Dashboard Window) (Default)
  [2] CLI (Command Line Terminal)
Enter choice (1-2) [Default: 1]: 1

[*] Launching Windows Tool Hub in [GUI] mode...
```

---

### Command-Line Direct Launch (Non-Interactive)

You can also pass arguments directly to `main.py` to skip prompts:

```bash
# Launch Windows GUI
python main.py --os windows --mode gui

# Launch Windows CLI tool list
python main.py --os windows --mode cli list

# Run Scan From Map on Windows via CLI
python main.py --os windows --mode cli scan_from_map "cafes in new york" --limit 10

# Run on Linux via CLI
python main.py --os linux --mode cli scan_from_map "dentists in london" --limit 15
```

---

## 📍 Available Tools

### 1. Scan From Map (`scan_from_map`)
- **Purpose**: Search Google Maps by any keyword to extract business listings.
- **Data Extracted**: Name, Phone Number, Website, Rating, Reviews Count, Category, Address, Hours/Status, Google Maps URL.
- **Editing**: Built-in data table with live search filtering, double-click editing modal, row addition, and deletion.
- **Exporting**: Export to CSV (`utf-8-sig` for Excel compatibility) and formatted TXT reports.
- **Browser Automation**: Automated via Playwright (supports Google Chrome and Microsoft Edge on Windows; Chromium/Chrome on Linux).

---

## 🧪 Testing

Run automated tests for each platform:

```bash
# Windows tests
python -m unittest windows.scan_from_map.test_app

# Linux tests
python -m unittest linux.scan_from_map.test_app
```

---

## ➕ Adding New Tools to the Hub

When adding a new tool:
1. Create a dedicated folder under `windows/<tool_name>/` and `linux/<tool_name>/`.
2. Keep all tool files, scripts, and `requirements.txt` inside that sandbox.
3. Register the new tool in `windows/app.py`, `windows/cli.py`, `linux/app.py`, and `linux/cli.py`.
4. It will immediately appear in the Master Launcher, Hub Dashboard, and CLI tool lists.
