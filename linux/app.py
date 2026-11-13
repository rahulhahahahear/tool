"""
Linux Tool Hub - Desktop Application
Unified GUI Dashboard to launch and manage scraping and automation tools on Linux.
Includes built-in dependency checker and installer for sandboxed tools.
"""

import sys
import os
import re
import threading
import subprocess
import importlib.metadata
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_tool_requirements_path(tool_id: str) -> str:
    req_path = os.path.join(BASE_DIR, tool_id, "requirements.txt")
    return req_path if os.path.exists(req_path) else ""


def check_missing_packages(tool_id: str) -> list:
    req_path = get_tool_requirements_path(tool_id)
    if not req_path:
        return []

    missing = []
    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[><=~!;]", line)[0].strip()
            if not pkg:
                continue
            try:
                importlib.metadata.version(pkg)
            except importlib.metadata.PackageNotFoundError:
                missing.append(pkg)
    return missing


def install_packages_worker(tool_id: str, on_done_cb):
    req_path = get_tool_requirements_path(tool_id)
    if not req_path:
        on_done_cb(True, "No requirements.txt found.")
        return

    cmd = [sys.executable, "-m", "pip", "install", "-r", req_path]
    try:
        subprocess.run(cmd, check=True)
        on_done_cb(True, f"All dependencies for '{tool_id}' installed successfully!")
    except Exception as e:
        on_done_cb(False, f"Failed to install dependencies:\n{e}")


def launch_scan_from_map(parent=None):
    """Launches the Scan From Map tool in its own window after checking dependencies."""
    missing = check_missing_packages("scan_from_map")
    if missing:
        confirm = messagebox.askyesno(
            "Missing Dependencies",
            f"The 'Scan From Map' tool requires uninstalled packages:\n{', '.join(missing)}\n\n"
            f"Would you like to install them automatically now?",
            parent=parent
        )
        if confirm:
            def on_installed(success, msg):
                if success:
                    messagebox.showinfo("Installation Complete", msg, parent=parent)
                    launch_scan_from_map(parent)
                else:
                    messagebox.showerror("Installation Error", msg, parent=parent)

            threading.Thread(target=install_packages_worker, args=("scan_from_map", on_installed), daemon=True).start()
        return

    try:
        from scan_from_map.app import GoogleMapsScraperApp

        top = tk.Toplevel(parent)
        app = GoogleMapsScraperApp(top)
        top.focus_force()
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to launch Scan From Map:\n{e}", parent=parent)


def launch_yt_data_scraper(parent=None):
    """Launches the YouTube Data Scraper tool in its own window on Linux."""
    missing = check_missing_packages("yt_data_scraper")
    if missing:
        confirm = messagebox.askyesno(
            "Missing Dependencies",
            f"The 'YouTube Data Scraper' tool requires uninstalled packages:\n{', '.join(missing)}\n\n"
            f"Would you like to install them automatically now?",
            parent=parent
        )
        if confirm:
            def on_installed(success, msg):
                if success:
                    messagebox.showinfo("Installation Complete", msg, parent=parent)
                    launch_yt_data_scraper(parent)
                else:
                    messagebox.showerror("Installation Error", msg, parent=parent)

            threading.Thread(target=install_packages_worker, args=("yt_data_scraper", on_installed), daemon=True).start()
        return

    try:
        from yt_data_scraper.app import YouTubeDataScraperApp

        top = tk.Toplevel(parent)
        app = YouTubeDataScraperApp(top)
        top.focus_force()
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to launch YouTube Data Scraper:\n{e}", parent=parent)


TOOL_MODULES = [
    {
        "id": "scan_from_map",
        "name": "Scan From Map",
        "icon": "📍",
        "badge": "Active",
        "badge_color": "#16a34a",
        "tags": ["Google Maps", "Scraper", "Editor", "CSV & TXT"],
        "description": (
            "Search Google Maps by keyword to extract business listings.\n"
            "Captures Name, Phone, Website, Rating, Reviews, Category, Address, and Hours.\n"
            "Optimized for Linux (Chromium / Google Chrome)."
        ),
        "cli_example": 'python linux/cli.py scan_from_map "cafes in london" --limit 15',
        "launch": launch_scan_from_map,
    },
    {
        "id": "yt_data_scraper",
        "name": "YouTube Data Scraper",
        "icon": "🔴",
        "badge": "Active",
        "badge_color": "#dc2626",
        "tags": ["YouTube", "Channels", "Subscribers Filter", "Leads", "CSV & TXT"],
        "description": (
            "Search YouTube by keyword to extract channel & video intelligence.\n"
            "Captures Channel Name, Subscribers, Handle, Contact Email, Website Links, and Source Video.\n"
            "Filter listings by subscriber count, edit records, and export with custom column selection."
        ),
        "cli_example": 'python linux/cli.py yt_data_scraper "tech reviews" --min-subscribers 10000',
        "launch": launch_yt_data_scraper,
    },
        ),
        "cli_example": "python linux/cli.py <tool_name> [options]",
        "launch": None,
    }
]


class LinuxToolHubApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Linux Automation & Scraping Tool Hub")
        self.root.geometry("980x680")
        self.root.minsize(800, 500)

        self._setup_styles()
        self._build_header()
        self._build_tools_view()
        self._build_footer()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("DejaVu Sans", 9))
        self.style.configure("Header.TLabel", font=("DejaVu Sans", 16, "bold"), foreground="#0f172a")
        self.style.configure("SubHeader.TLabel", font=("DejaVu Sans", 10), foreground="#64748b")
        self.style.configure(
            "Primary.TButton",
            font=("DejaVu Sans", 9, "bold"),
            foreground="#ffffff",
            background="#2563eb",
            padding=6
        )
        self.style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#94a3b8")])

    def _build_header(self):
        header_frame = ttk.Frame(self.root, padding="20 15 20 10")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="🐧  Linux Automation & Tool Hub", style="Header.TLabel")
        title_lbl.pack(anchor="w")

        sub_lbl = ttk.Label(
            header_frame,
            text="Central launcher and workspace manager for Linux scraping & automation tools.",
            style="SubHeader.TLabel"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        sep = ttk.Separator(self.root, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=20, pady=(5, 12))

    def _build_tools_view(self):
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0, bg="#f8fafc")
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scroll_content = ttk.Frame(canvas)

        self.scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for tool in TOOL_MODULES:
            self._create_tool_card(self.scroll_content, tool)

    def _create_tool_card(self, parent, tool: dict):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID, padx=16, pady=14)
        card.pack(fill=tk.X, pady=8, padx=4)

        top_row = tk.Frame(card, bg="#ffffff")
        top_row.pack(fill=tk.X)

        icon_lbl = tk.Label(top_row, text=tool["icon"], font=("DejaVu Sans", 16), bg="#ffffff")
        icon_lbl.pack(side=tk.LEFT, padx=(0, 8))

        name_lbl = tk.Label(top_row, text=tool["name"], font=("DejaVu Sans", 12, "bold"), fg="#0f172a", bg="#ffffff")
        name_lbl.pack(side=tk.LEFT)

        missing = check_missing_packages(tool["id"]) if tool.get("launch") else []
        badge_text = f"  {tool['badge']}  " if not missing else f"  Missing Deps: {', '.join(missing)}  "
        badge_bg = tool["badge_color"] if not missing else "#dc2626"

        badge_lbl = tk.Label(
            top_row,
            text=badge_text,
            font=("DejaVu Sans", 8, "bold"),
            fg="#ffffff",
            bg=badge_bg,
            padx=4,
            pady=1
        )
        badge_lbl.pack(side=tk.RIGHT)

        tags_row = tk.Frame(card, bg="#ffffff")
        tags_row.pack(fill=tk.X, pady=(6, 4))
        for tag in tool.get("tags", []):
            t_lbl = tk.Label(tags_row, text=f" #{tag} ", font=("DejaVu Sans", 8), fg="#475569", bg="#f1f5f9", padx=4)
            t_lbl.pack(side=tk.LEFT, padx=(0, 4))

        desc_lbl = tk.Label(
            card,
            text=tool["description"],
            font=("DejaVu Sans", 9),
            fg="#334155",
            bg="#ffffff",
            justify=tk.LEFT,
            anchor="w"
        )
        desc_lbl.pack(fill=tk.X, pady=(4, 10))

        bottom_row = tk.Frame(card, bg="#ffffff")
        bottom_row.pack(fill=tk.X)

        cli_lbl = tk.Label(
            bottom_row,
            text=f"CLI: {tool['cli_example']}",
            font=("Monospace", 8),
            fg="#64748b",
            bg="#ffffff"
        )
        cli_lbl.pack(side=tk.LEFT)

        btn_box = tk.Frame(bottom_row, bg="#ffffff")
        btn_box.pack(side=tk.RIGHT)

        if tool.get("launch"):
            launch_btn = ttk.Button(
                btn_box,
                text="🚀 Launch Tool",
                style="Primary.TButton",
                command=lambda t=tool: t["launch"](self.root)
            )
            launch_btn.pack(side=tk.RIGHT)

            if missing:
                install_btn = ttk.Button(
                    btn_box,
                    text="📦 Install Deps",
                    command=lambda t=tool: self._install_tool_deps(t["id"])
                )
                install_btn.pack(side=tk.RIGHT, padx=4)

            info_btn = ttk.Button(
                btn_box,
                text="ℹ️ Info",
                command=lambda t=tool: self._show_tool_info(t)
            )
            info_btn.pack(side=tk.RIGHT, padx=6)
        else:
            wait_btn = ttk.Button(
                btn_box,
                text="⏳ Awaiting Plan",
                state=tk.DISABLED
            )
            wait_btn.pack(side=tk.RIGHT)

    def _install_tool_deps(self, tool_id: str):
        def on_done(success, msg):
            if success:
                messagebox.showinfo("Installed", msg, parent=self.root)
            else:
                messagebox.showerror("Error", msg, parent=self.root)

        threading.Thread(target=install_packages_worker, args=(tool_id, on_done), daemon=True).start()

    def _show_tool_info(self, tool: dict):
        req_path = get_tool_requirements_path(tool["id"])
        missing = check_missing_packages(tool["id"])
        dep_info = "All packages installed" if not missing else f"Missing: {', '.join(missing)}"

        info_msg = (
            f"Tool: {tool['name']}\n"
            f"Module: {tool['id']}\n"
            f"Dependencies: {dep_info}\n"
            f"Requirements file: {req_path or 'None'}\n\n"
            f"Description:\n{tool['description']}\n\n"
            f"Command Line Usage:\n{tool['cli_example']}\n\n"
            f"Folder Location:\nlinux/{tool['id']}/"
        )
        messagebox.showinfo(f"{tool['name']} - Details", info_msg)

    def _build_footer(self):
        footer = ttk.Frame(self.root, padding="15 10")
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        left_lbl = ttk.Label(
            footer,
            text=f"Python {sys.version.split()[0]} | Linux Hub",
            font=("DejaVu Sans", 8),
            foreground="#64748b"
        )
        left_lbl.pack(side=tk.LEFT)

        install_all_btn = ttk.Button(footer, text="📦 Install All Dependencies", command=self._install_all_deps)
        install_all_btn.pack(side=tk.RIGHT, padx=4)

    def _install_all_deps(self):
        confirm = messagebox.askyesno(
            "Install All Dependencies",
            "This will check and install dependencies for all registered Linux tools in the hub.\nDo you want to proceed?",
            parent=self.root
        )
        if confirm:
            def worker():
                for tool in TOOL_MODULES:
                    if tool.get("launch"):
                        req_path = get_tool_requirements_path(tool["id"])
                        if req_path:
                            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_path])
                messagebox.showinfo("Done", "Finished installing all dependencies!", parent=self.root)

            threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    app = LinuxToolHubApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
