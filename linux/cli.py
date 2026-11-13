"""
Linux Tool Hub - Command Line Interface (CLI)
Provides a unified interface to list, inspect, and run all tools on Linux.
"""

import sys
import os
import importlib

# Tool registry for Linux
TOOLS = {
    "scan_from_map": {
        "name": "Scan From Map (Linux)",
        "description": "Scrape Google Maps business listings (Name, Phone, Website, Address, Rating, etc.) with CSV & TXT export.",
        "module": "scan_from_map.cli",
        "entry": "main",
        "status": "Ready",
    }
}


def print_banner():
    print("=" * 65)
    print("      🐧  AUTOMATION & SCRAPING TOOL HUB (LINUX CLI)")
    print("=" * 65)


def list_tools():
    print_banner()
    print("\nAvailable Tools in Linux Hub:\n")
    for tool_id, meta in TOOLS.items():
        print(f"  [{meta['status']}] {tool_id}")
        print(f"       Name:        {meta['name']}")
        print(f"       Description: {meta['description']}")
        print(f"       Usage:       python linux/cli.py {tool_id} [options]\n")
    print("Run `python linux/cli.py <tool_name> --help` for specific tool options.")
    print("=" * 65)


def run_tool(tool_id, tool_args):
    if tool_id not in TOOLS:
        print(f"Error: Tool '{tool_id}' not found in Linux hub.")
        print(f"Available tools: {', '.join(TOOLS.keys())}")
        sys.exit(1)

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
        print("  python linux/cli.py list                      List all registered tools")
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

    # Run tool
    tool_id = command
    tool_args = args[1:]
    run_tool(tool_id, tool_args)


if __name__ == "__main__":
    main()
