"""
Master Universal Launcher for Tool Hub
Prompts for OS (Windows or Linux) and Interface (GUI or CLI), then launches the selected tool hub.
"""

import sys
import os
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def print_banner():
    print("=" * 66)
    print("      🛠️  AUTOMATION & SCRAPING TOOL HUB - MASTER LAUNCHER")
    print("=" * 66)


def ask_choice(prompt_text: str, options: list, default_index: int = 0) -> int:
    """Helper to prompt user for a numbered option."""
    print(f"\n{prompt_text}")
    for idx, opt in enumerate(options, 1):
        default_tag = " (Default)" if idx - 1 == default_index else ""
        print(f"  [{idx}] {opt}{default_tag}")

    while True:
        choice = input(f"Enter choice (1-{len(options)}) [Default: {default_index + 1}]: ").strip()
        if not choice:
            return default_index
        if choice.isdigit():
            c_int = int(choice)
            if 1 <= c_int <= len(options):
                return c_int - 1
        print(f"Invalid input. Please enter a number between 1 and {len(options)}.")


def launch_windows(mode: str, extra_args=None):
    win_dir = os.path.join(BASE_DIR, "windows")
    if win_dir not in sys.path:
        sys.path.insert(0, win_dir)

    print(f"\n[*] Launching Windows Tool Hub in [{mode.upper()}] mode...\n")
    if mode == "gui":
        import app as win_app
        win_app.main()
    else:
        import cli as win_cli
        win_cli.main(extra_args)


def launch_linux(mode: str, extra_args=None):
    linux_dir = os.path.join(BASE_DIR, "linux")
    if linux_dir not in sys.path:
        sys.path.insert(0, linux_dir)

    print(f"\n[*] Launching Linux Tool Hub in [{mode.upper()}] mode...\n")
    if mode == "gui":
        import app as linux_app
        linux_app.main()
    else:
        import cli as linux_cli
        linux_cli.main(extra_args)


def main():
    print_banner()

    # Check for direct command-line arguments (e.g. python main.py --os windows --mode gui)
    args = sys.argv[1:]
    target_os = None
    target_mode = None
    remaining_args = []

    i = 0
    while i < len(args):
        if args[i] in ("--os", "-o") and i + 1 < len(args):
            target_os = args[i + 1].lower()
            i += 2
        elif args[i] in ("--mode", "-m") and i + 1 < len(args):
            target_mode = args[i + 1].lower()
            i += 2
        elif args[i] in ("windows", "win"):
            target_os = "windows"
            i += 1
        elif args[i] in ("linux", "lin"):
            target_os = "linux"
            i += 1
        elif args[i] in ("gui", "cli"):
            target_mode = args[i]
            i += 1
        else:
            remaining_args.append(args[i])
            i += 1

    # Detect current host platform
    is_win = platform.system().lower().startswith("win")
    default_os_idx = 0 if is_win else 1

    # 1. Ask OS if not provided
    if not target_os:
        os_options = [
            f"Windows{' (Current Host)' if is_win else ''}",
            f"Linux{' (Current Host)' if not is_win else ''}"
        ]
        chosen_os_idx = ask_choice(
            "[?] Step 1: Select Operating System Platform:",
            os_options,
            default_index=default_os_idx
        )
        target_os = "windows" if chosen_os_idx == 0 else "linux"

    # 2. Ask Mode (CLI, GUI, or Install Dependencies) if not provided
    if not target_mode:
        mode_options = [
            "GUI (Desktop Dashboard Window)",
            "CLI (Command Line Terminal)",
            "📦 Install / Verify Dependencies (Tool Requirements)"
        ]
        chosen_mode_idx = ask_choice(
            "[?] Step 2: Select Action:",
            mode_options,
            default_index=0
        )
        if chosen_mode_idx == 0:
            target_mode = "gui"
        elif chosen_mode_idx == 1:
            target_mode = "cli"
        else:
            target_mode = "install"

    # 3. Launch according to instructions
    if target_mode == "install":
        args_to_pass = ["install"] + (remaining_args if remaining_args else ["all"])
        if target_os.startswith("win"):
            launch_windows("cli", args_to_pass)
        else:
            launch_linux("cli", args_to_pass)
    elif target_os.startswith("win"):
        launch_windows(target_mode, remaining_args if target_mode == "cli" else None)
    else:
        launch_linux(target_mode, remaining_args if target_mode == "cli" else None)


if __name__ == "__main__":
    main()
