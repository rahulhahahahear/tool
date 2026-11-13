"""
Central Tool Hub - Desktop Application
Unified GUI Dashboard to launch and manage scraping and automation tools.
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox


def launch_scan_from_map(parent=None):
    """Launches the Scan From Map tool in its own window."""
    try:
        from scan_from_map.app import GoogleMapsScraperApp

        top = tk.Toplevel(parent)
        app = GoogleMapsScraperApp(top)
        top.focus_force()
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to launch Scan From Map:\n{e}")


# Registry of available tools in the Hub
TOOL_MODULES = [
    {
        "id": "scan_from_map",
        "name": "Scan From Map",
        "icon": "📍",
        "badge": "Active",
        "badge_color": "#16a34a",  # Green
        "tags": ["Google Maps", "Scraper", "Editor", "CSV & TXT"],
        "description": (
            "Search Google Maps by keyword to extract business listings.\n"
            "Captures Name, Phone, Website, Rating, Reviews, Category, Address, and Hours.\n"
            "Includes live table filtering, inline editing dialog, and one-click export to CSV & TXT."
        ),
        "cli_example": 'python cli.py scan_from_map "cafes in new york" --limit 15',
        "launch": launch_scan_from_map,
    },
    {
        "id": "upcoming_tool_2",
        "name": "Tool Slot #2 (Upcoming)",
        "icon": "⚡",
        "badge": "Pending Spec",
        "badge_color": "#d97706",  # Amber
        "tags": ["Next Module", "In Development"],
        "description": (
            "Slot reserved for your next automation / scraping tool.\n"
            "Ready to be plugged in as soon as you provide the specifications."
        ),
        "cli_example": "python cli.py <tool_name> [options]",
        "launch": None,
    },
    {
        "id": "upcoming_tool_3",
        "name": "Tool Slot #3 (Upcoming)",
        "icon": "🔮",
        "badge": "Reserved",
        "badge_color": "#64748b",  # Slate
        "tags": ["Future Expansion"],
        "description": (
            "Additional reserved slot for future tools in the hub."
        ),
        "cli_example": "python cli.py <tool_name> [options]",
        "launch": None,
    }
]


class ToolHubApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("All-in-One Automation & Tool Hub")
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

        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0f172a")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#64748b")
        self.style.configure("CardTitle.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1e293b")
        self.style.configure("CardDesc.TLabel", font=("Segoe UI", 9), foreground="#334155")
        self.style.configure("Tag.TLabel", font=("Segoe UI", 8, "bold"), foreground="#2563eb", background="#eff6ff")

        # Action Buttons
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            foreground="#ffffff",
            background="#2563eb",
            padding=6
        )
        self.style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#94a3b8")])

    def _build_header(self):
        header_frame = ttk.Frame(self.root, padding="20 15 20 10")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="🛠️  Automation & Scraping Tool Hub", style="Header.TLabel")
        title_lbl.pack(anchor="w")

        sub_lbl = ttk.Label(
            header_frame,
            text="Central launcher and workspace manager for all specialized scraping & automation tools.",
            style="SubHeader.TLabel"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        sep = ttk.Separator(self.root, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=20, pady=(5, 12))

    def _build_tools_view(self):
        # Scrollable container for cards
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

        # Build each card
        for tool in TOOL_MODULES:
            self._create_tool_card(self.scroll_content, tool)

    def _create_tool_card(self, parent, tool: dict):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID, padx=16, pady=14)
        card.pack(fill=tk.X, pady=8, padx=4)

        # Top row: Icon + Name + Badge
        top_row = tk.Frame(card, bg="#ffffff")
        top_row.pack(fill=tk.X)

        icon_lbl = tk.Label(top_row, text=tool["icon"], font=("Segoe UI Emoji", 16), bg="#ffffff")
        icon_lbl.pack(side=tk.LEFT, padx=(0, 8))

        name_lbl = tk.Label(top_row, text=tool["name"], font=("Segoe UI", 12, "bold"), fg="#0f172a", bg="#ffffff")
        name_lbl.pack(side=tk.LEFT)

        badge_lbl = tk.Label(
            top_row,
            text=f"  {tool['badge']}  ",
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg=tool["badge_color"],
            padx=4,
            pady=1
        )
        badge_lbl.pack(side=tk.RIGHT)

        # Tags row
        tags_row = tk.Frame(card, bg="#ffffff")
        tags_row.pack(fill=tk.X, pady=(6, 4))
        for tag in tool.get("tags", []):
            t_lbl = tk.Label(tags_row, text=f" #{tag} ", font=("Segoe UI", 8), fg="#475569", bg="#f1f5f9", padx=4)
            t_lbl.pack(side=tk.LEFT, padx=(0, 4))

        # Description
        desc_lbl = tk.Label(
            card,
            text=tool["description"],
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#ffffff",
            justify=tk.LEFT,
            anchor="w"
        )
        desc_lbl.pack(fill=tk.X, pady=(4, 10))

        # Bottom row: CLI Example & Launch Button
        bottom_row = tk.Frame(card, bg="#ffffff")
        bottom_row.pack(fill=tk.X)

        cli_lbl = tk.Label(
            bottom_row,
            text=f"CLI: {tool['cli_example']}",
            font=("Consolas", 8),
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

    def _show_tool_info(self, tool: dict):
        info_msg = (
            f"Tool: {tool['name']}\n"
            f"Module: {tool['id']}\n"
            f"Status: {tool['badge']}\n\n"
            f"Description:\n{tool['description']}\n\n"
            f"Command Line Usage:\n{tool['cli_example']}\n\n"
            f"Folder Location:\n.\\{tool['id']}\\"
        )
        messagebox.showinfo(f"{tool['name']} - Details", info_msg)

    def _build_footer(self):
        footer = ttk.Frame(self.root, padding="15 10")
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        left_lbl = ttk.Label(
            footer,
            text=f"Python {sys.version.split()[0]} | Working Dir: {os.path.basename(os.getcwd())}",
            style="Muted.TLabel"
        )
        left_lbl.pack(side=tk.LEFT)

        open_folder_btn = ttk.Button(footer, text="📂 Open Tool Folder", command=self._open_workspace)
        open_folder_btn.pack(side=tk.RIGHT, padx=4)

    def _open_workspace(self):
        try:
            os.startfile(os.getcwd())
        except Exception:
            pass


def main():
    root = tk.Tk()
    app = ToolHubApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
