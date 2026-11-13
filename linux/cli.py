"""
Linux Tool Hub - Command Line Interface (CLI)
Provides a unified interface to list, inspect, manage dependencies, and run all tools on Linux.
"""

import sys
import os
import re
import subprocess
import importlib
import importlib.metadata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOOLS = {
    "scan_from_map": {
        "name": "Scan From Map (Linux)",
        "folder": "scan_from_map",
        "description": "Scrape Google Maps business listings (Name, Phone, Website, Address, Rating, etc.) with CSV & TXT export.",
        "module": "scan_from_map.cli",
        "entry": "main",
        "status": "Ready",
    },
    "yt_data_scraper": {
        "name": "YouTube Data Scraper (Linux)",
        "folder": "yt_data_scraper",
        "description": "Scrape YouTube channels & videos (Name, Subscribers, Handle, Contact/Email, Website, Source Video, etc.) with custom column CSV/TXT export.",
        "module": "yt_data_scraper.cli",
        "entry": "main",
        "status": "Ready",
    }
}


def print_banner():
    print("=" * 65)
    print("      🐧  AUTOMATION & SCRAPING TOOL HUB (LINUX CLI)")
    print("=" * 65)


def get_tool_requirements_path(tool_id: str) -> str:
    meta = TOOLS.get(tool_id)
    if not meta:
        return ""
    folder = meta.get("folder", tool_id)
    req_path = os.path.join(BASE_DIR, folder, "requirements.txt")
    return req_path if os.path.exists(req_path) else ""


def check_missing_dependencies(tool_id: str) -> list:
    req_path = get_tool_requirements_path(tool_id)
    if not req_path:
        return []

    missing = []
    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            pkg_name = re.split(r"[><=~!;]", line)[0].strip()
            if not pkg_name:
                continue

            try:
                importlib.metadata.version(pkg_name)
            except importlib.metadata.PackageNotFoundError:
                missing.append(pkg_name)

    return missing


def install_dependencies(tool_id: str) -> bool:
    req_path = get_tool_requirements_path(tool_id)
    if not req_path:
        print(f"[*] No requirements.txt found for tool '{tool_id}'.")
        return True

    print(f"\n[*] Installing dependencies for '{tool_id}' from: {req_path}")
    cmd = [sys.executable, "-m", "pip", "install", "-r", req_path]
    try:
        res = subprocess.run(cmd, check=True)
        print(f"[+] Dependencies for '{tool_id}' installed successfully!\n")
        return res.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[!] Error installing dependencies for '{tool_id}': {e}\n")
        return False


def install_all_dependencies():
    print_banner()
    print("\n[*] Installing dependencies for all registered Linux tools...\n")
    for tool_id in TOOLS:
        install_dependencies(tool_id)
    print("[+] All Linux tool dependencies check completed.\n")


def list_tools():
    print_banner()
    print("\nAvailable Tools in Linux Hub:\n")
    for tool_id, meta in TOOLS.items():
        missing = check_missing_dependencies(tool_id)
        dep_status = "Dependencies OK" if not missing else f"Missing: {', '.join(missing)}"
        print(f"  [{meta['status']}] {tool_id} ({dep_status})")
        print(f"       Name:        {meta['name']}")
        print(f"       Description: {meta['description']}")
        print(f"       Usage:       python linux/cli.py {tool_id} [options]\n")
    print("Commands:")
    print("  python linux/cli.py install <tool_name>       Install dependencies for a specific tool")
    print("  python linux/cli.py install all               Install dependencies for all tools")
    print("  python linux/cli.py <tool_name> --help        Show tool-specific options")
    print("=" * 65)


def run_tool(tool_id: str, tool_args: list):
    if tool_id not in TOOLS:
        print(f"Error: Tool '{tool_id}' not found in Linux hub.")
        print(f"Available tools: {', '.join(TOOLS.keys())}")
        sys.exit(1)

    missing = check_missing_dependencies(tool_id)
    if missing:
        print(f"\n[!] Tool '{tool_id}' requires missing packages: {', '.join(missing)}")
        choice = input(f"[?] Would you like to install them automatically now? (Y/n): ").strip().lower()
        if choice in ("", "y", "yes"):
            success = install_dependencies(tool_id)
            if not success:
                print("[!] Aborting tool launch due to dependency installation failure.")
                sys.exit(1)
        else:
            print(f"[!] Warning: Running tool without required packages: {missing}")

    meta = TOOLS[tool_id]
    try:
        mod = importlib.import_module(meta["module"])
        entry_func = getattr(mod, meta["entry"])
        return entry_func(tool_args)
    except Exception as e:
        print(f"Error running tool '{tool_id}': {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main(custom_args=None):
    args = custom_args if custom_args is not None else sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        if len(args) == 2 and args[0] == "help":
            run_tool(args[1], ["--help"])
            return
        print_banner()
        print("\nUsage:")
        print("  python linux/cli.py list                      List all registered tools and dependency status")
        print("  python linux/cli.py install <tool_name>       Install dependencies for a specific tool")
        print("  python linux/cli.py install all               Install dependencies for all tools")
        print("  python linux/cli.py <tool_name> [options]     Run a specific tool")
        print("  python linux/cli.py help <tool_name>          Show help for a specific tool\n")
        print("Example:")
        print('  python linux/cli.py scan_from_map "coffee in new york" --limit 10')
        print("=" * 65)
        return

    command = args[0].lower()

    if command in ("list", "--list", "-l"):
        list_tools()
        return

    if command == "install":
        target = args[1].lower() if len(args) > 1 else "all"
        if target in ("all", "--all"):
            install_all_dependencies()
        elif target in TOOLS:
            install_dependencies(target)
        else:
            print(f"Unknown tool '{target}'. Available tools: {', '.join(TOOLS.keys())} or 'all'")
        return

    # Run tool
    tool_id = command
    tool_args = args[1:]
    run_tool(tool_id, tool_args)


if __name__ == "__main__":
    main()
