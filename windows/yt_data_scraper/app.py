"""
YouTube Data Scraper - Interactive Desktop GUI Application
Searches YouTube by keyword, extracts channel & video details, filters by subscribers,
edits listings, and exports with custom column selection to CSV/TXT.
"""

import sys
import os
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional

try:
    from .scraper import YouTubeDataScraper, parse_subscribers_to_number
    from .exporter import export_to_csv, export_to_txt
except (ImportError, ValueError):
    from scraper import YouTubeDataScraper, parse_subscribers_to_number
    from exporter import export_to_csv, export_to_txt


class ColumnSelectorDialog(tk.Toplevel):
    """Modal dialog allowing user to choose which columns to export."""

    def __init__(self, parent, available_columns, on_confirm, title="Select Columns to Export"):
        super().__init__(parent)
        self.available_columns = available_columns
        self.on_confirm = on_confirm
        self.title(title)
        self.geometry("380x480")
        self.minsize(320, 380)
        self.transient(parent)
        self.grab_set()

        self.check_vars = {}
        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Select Columns to Export", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Choose which fields to include in your output file:", font=("Segoe UI", 9), foreground="#64748b").pack(anchor="w", pady=(2, 10))

        sel_row = ttk.Frame(frame)
        sel_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(sel_row, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(sel_row, text="Deselect All", command=self._deselect_all).pack(side=tk.LEFT)

        cols_frame = ttk.Frame(frame, padding="6", relief=tk.GROOVE)
        cols_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        for col in self.available_columns:
            var = tk.BooleanVar(value=True)
            self.check_vars[col] = var
            cb = ttk.Checkbutton(cols_frame, text=col, variable=var)
            cb.pack(anchor="w", pady=2, padx=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Export Now", style="Accent.TButton", command=self._confirm).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _select_all(self):
        for v in self.check_vars.values():
            v.set(True)

    def _deselect_all(self):
        for v in self.check_vars.values():
            v.set(False)

    def _confirm(self):
        chosen = [col for col, var in self.check_vars.items() if var.get()]
        if not chosen:
            messagebox.showwarning("No Columns", "Please select at least one column to export.", parent=self)
            return
        self.destroy()
        self.on_confirm(chosen)


class EditChannelDialog(tk.Toplevel):
    """Modal dialog to edit or create a YouTube channel record."""

    def __init__(self, parent, item_data: Optional[Dict[str, Any]] = None, on_save=None):
        super().__init__(parent)
        self.item_data = item_data or {}
        self.on_save = on_save

        self.title("Edit Channel Details" if item_data else "Add New Channel")
        self.geometry("560x600")
        self.minsize(480, 500)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._populate_fields()
        self._center()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            frame,
            text="Channel Information" if self.item_data else "Add New Channel",
            font=("Segoe UI", 12, "bold")
        )
        header.pack(anchor="w", pady=(0, 15))

        form_frame = ttk.Frame(frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        self.entries = {}
        fields = [
            ("name", "Channel Name *"),
            ("handle", "Handle (@...)"),
            ("subscribers", "Subscribers (e.g. 1.2M)"),
            ("videos_count", "Video Count"),
            ("contact", "Contact / Email"),
            ("website", "Website / Links"),
            ("video_title", "Source Video Title"),
            ("video_url", "Source Video URL"),
            ("channel_url", "Channel URL"),
            ("description", "Description / Bio"),
        ]

        for i, (key, label) in enumerate(fields):
            lbl = ttk.Label(form_frame, text=label, font=("Segoe UI", 9))
            lbl.grid(row=i, column=0, sticky="w", pady=4, padx=(0, 10))

            entry = ttk.Entry(form_frame, font=("Segoe UI", 9))
            entry.grid(row=i, column=1, sticky="ew", pady=4)
            self.entries[key] = entry

        form_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        save_btn = ttk.Button(btn_frame, text="💾 Save Changes", command=self._on_save, style="Accent.TButton")
        save_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _populate_fields(self):
        for key, entry in self.entries.items():
            val = self.item_data.get(key, "")
            entry.insert(0, str(val) if val is not None else "")

    def _on_save(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Channel Name is required.", parent=self)
            return

        updated_data = {key: self.entries[key].get().strip() for key in self.entries}
        # Update numeric subscriber count
        updated_data["subscribers_count"] = parse_subscribers_to_number(updated_data.get("subscribers", ""))
        if self.on_save:
            self.on_save(updated_data)
        self.destroy()


class YouTubeDataScraperApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YouTube Data Scraper - Lead & Channel Finder")
        self.root.geometry("1200x720")
        self.root.minsize(920, 560)

        self.records: List[Dict[str, Any]] = []
        self.active_scraper: Optional[YouTubeDataScraper] = None
        self.is_scraping = False
        self.current_query = ""

        self._setup_styles()
        self._build_search_panel()
        self._build_filters_panel()
        self._build_table_panel()
        self._build_toolbar()
        self._build_status_bar()

        # Keyboard shortcuts
        self.root.bind("<Control-f>", lambda e: self.filter_entry.focus())
        self.root.bind("<Control-s>", lambda e: self._export_csv())
        self.root.bind("<F5>", lambda e: self._start_scraping())

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground="#1e293b")
        self.style.configure("Muted.TLabel", font=("Segoe UI", 8), foreground="#64748b")

        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 9, "bold"),
            foreground="#ffffff",
            background="#dc2626",  # YouTube Red
            padding=6
        )
        self.style.map("Accent.TButton", background=[("active", "#b91c1c"), ("disabled", "#94a3b8")])

        self.style.configure(
            "Stop.TButton",
            font=("Segoe UI", 9, "bold"),
            foreground="#ffffff",
            background="#475569",
            padding=6
        )
        self.style.map("Stop.TButton", background=[("active", "#334155"), ("disabled", "#94a3b8")])

        self.style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=26,
            background="#ffffff",
            fieldbackground="#ffffff"
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#f1f5f9",
            foreground="#0f172a",
            relief="flat"
        )
        self.style.map("Treeview", background=[("selected", "#dc2626")], foreground=[("selected", "#ffffff")])

    def _build_search_panel(self):
        container = ttk.LabelFrame(self.root, text="YouTube Search Settings", padding="12")
        container.pack(fill=tk.X, padx=12, pady=(10, 4))

        r1 = ttk.Frame(container)
        r1.pack(fill=tk.X)

        ttk.Label(r1, text="Keyword / Topic:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.keyword_entry = ttk.Entry(r1, font=("Segoe UI", 10), width=30)
        self.keyword_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.keyword_entry.insert(0, "tech reviews")
        self.keyword_entry.bind("<Return>", lambda e: self._start_scraping())

        ttk.Label(r1, text="Search Mode:").pack(side=tk.LEFT, padx=(0, 5))
        self.mode_combo = ttk.Combobox(r1, values=["Both (Channels + Top Videos)", "Channels Only", "Videos Only"], width=24, state="readonly")
        self.mode_combo.set("Both (Channels + Top Videos)")
        self.mode_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(r1, text="Limit:").pack(side=tk.LEFT, padx=(0, 5))
        self.limit_combo = ttk.Combobox(r1, values=["10", "20", "50", "100"], width=5, state="readonly")
        self.limit_combo.set("15")
        self.limit_combo.pack(side=tk.LEFT, padx=(0, 15))

        self.deep_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(r1, text="Fetch About Links & Emails", variable=self.deep_var).pack(side=tk.LEFT, padx=(0, 15))

        self.start_btn = ttk.Button(r1, text="🔍 Scrape YouTube", command=self._start_scraping, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = ttk.Button(r1, text="⏹ Stop", command=self._stop_scraping, style="Stop.TButton", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

    def _build_filters_panel(self):
        container = ttk.Frame(self.root, padding="12 4")
        container.pack(fill=tk.X)

        # Quick text search
        ttk.Label(container, text="🔎 Quick Text Filter:").pack(side=tk.LEFT, padx=(0, 6))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *args: self._apply_filters())
        self.filter_entry = ttk.Entry(container, textvariable=self.filter_var, font=("Segoe UI", 9), width=24)
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 15))

        # Subscriber filter
        ttk.Label(container, text="Min Subscribers:").pack(side=tk.LEFT, padx=(0, 4))
        self.min_sub_combo = ttk.Combobox(container, values=["Any", "1,000", "5,000", "10,000", "50,000", "100,000", "500,000", "1,000,000"], width=10, state="readonly")
        self.min_sub_combo.set("Any")
        self.min_sub_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
        self.min_sub_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(container, text="Reset Filters", command=self._reset_filters).pack(side=tk.LEFT)

        # Stats
        self.stats_lbl = ttk.Label(container, text="Total Channels: 0", font=("Segoe UI", 9, "bold"), foreground="#dc2626")
        self.stats_lbl.pack(side=tk.RIGHT)

        hint = ttk.Label(container, text="(Double-click any row to edit)", style="Muted.TLabel")
        hint.pack(side=tk.RIGHT, padx=12)

    def _reset_filters(self):
        self.filter_var.set("")
        self.min_sub_combo.set("Any")
        self._apply_filters()

    def _build_table_panel(self):
        table_frame = ttk.Frame(self.root, padding="12 0")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("idx", "name", "handle", "subscribers", "videos", "contact", "website", "video_title", "channel_url")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        headings = [
            ("idx", "#", 45, "center"),
            ("name", "Channel Name", 180, "w"),
            ("handle", "Handle", 120, "w"),
            ("subscribers", "Subscribers", 110, "center"),
            ("videos", "Videos", 90, "center"),
            ("contact", "Contact / Email", 170, "w"),
            ("website", "Website / Links", 170, "w"),
            ("video_title", "Discovered Video Title", 220, "w"),
            ("channel_url", "Channel URL", 200, "w"),
        ]

        for col, title, width, anchor in headings:
            self.tree.heading(col, text=title, command=lambda c=col: self._sort_column(c, False))
            self.tree.column(col, width=width, anchor=anchor, stretch=(col in ("name", "website", "video_title", "channel_url")))

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("oddrow", background="#f8fafc")
        self.tree.tag_configure("evenrow", background="#ffffff")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected_record())
        self.tree.bind("<Return>", lambda e: self._edit_selected_record())

        self._build_context_menu()

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="✏️ Edit Channel...", command=self._edit_selected_record)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔴 Open Channel on YouTube", command=self._open_channel)
        self.context_menu.add_command(label="▶️ Open Source Video", command=self._open_video)
        self.context_menu.add_command(label="🌐 Open External Website", command=self._open_website)
        self.context_menu.add_command(label="📋 Copy Email / Contact", command=self._copy_contact)
        self.context_menu.add_command(label="📋 Copy Channel Link", command=self._copy_channel_link)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ Delete Selected", command=self._delete_selected_record)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, padding="12 8")
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="✏️ Edit Selected", command=self._edit_selected_record).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="➕ Add Channel", command=self._add_new_record).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🗑️ Delete Selected", command=self._delete_selected_record).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🧹 Clear All", command=self._clear_all_records).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="💾 Export to CSV", command=self._export_csv, style="Accent.TButton").pack(side=tk.RIGHT, padx=4)
        ttk.Button(toolbar, text="📄 Export to TXT", command=self._export_txt).pack(side=tk.RIGHT, padx=4)

    def _build_status_bar(self):
        bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding="6 4")
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_bar = ttk.Progressbar(bar, orient=tk.HORIZONTAL, mode="determinate", length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 5))

        self.status_lbl = ttk.Label(bar, text="Ready. Enter a keyword to start scraping YouTube channels.", anchor="w")
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # -------------------------------------------------------------
    # Scraping Logic
    # -------------------------------------------------------------
    def _start_scraping(self):
        if self.is_scraping:
            return

        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Input Required", "Please enter a keyword to search.")
            self.keyword_entry.focus()
            return

        try:
            limit = int(self.limit_combo.get().strip())
        except ValueError:
            limit = 15

        mode_str = self.mode_combo.get().lower()
        if "channel" in mode_str and "video" not in mode_str:
            search_mode = "channels"
        elif "video" in mode_str and "channel" not in mode_str:
            search_mode = "videos"
        else:
            search_mode = "both"

        deep_fetch = self.deep_var.get()
        self.current_query = keyword

        self.is_scraping = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = limit
        self.status_lbl.config(text=f"Searching YouTube for '{keyword}'...")

        self.active_scraper = YouTubeDataScraper(
            headless=True,
            preferred_channel="chrome",
            fetch_channel_details=deep_fetch,
            on_progress=self._thread_on_progress,
            on_item_scraped=self._thread_on_item_scraped
        )

        threading.Thread(target=self._run_scraper_worker, args=(keyword, limit, search_mode), daemon=True).start()

    def _stop_scraping(self):
        if self.active_scraper and self.is_scraping:
            self.status_lbl.config(text="Stopping scraper...")
            self.active_scraper.request_stop()
            self.stop_btn.configure(state=tk.DISABLED)

    def _run_scraper_worker(self, keyword: str, limit: int, search_mode: str):
        try:
            self.active_scraper.scrape(keyword, max_results=limit, search_mode=search_mode)
        except Exception as e:
            self.root.after(0, self._thread_on_error, str(e))
        finally:
            self.root.after(0, self._thread_on_finish)

    def _thread_on_progress(self, msg: str):
        self.root.after(0, self._update_status, msg)

    def _thread_on_item_scraped(self, item: Dict[str, Any], current: int, total: int):
        self.root.after(0, self._add_or_update_scraped_item, item, current, total)

    def _thread_on_error(self, err_msg: str):
        messagebox.showerror("Scraping Error", f"An error occurred while scraping:\n{err_msg}")

    def _thread_on_finish(self):
        self.is_scraping = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress_bar["value"] = self.progress_bar["maximum"]
        self.status_lbl.config(text=f"Scraping completed! Total records: {len(self.records)}")
        self._refresh_table()

    def _update_status(self, msg: str):
        self.status_lbl.config(text=msg)

    def _add_or_update_scraped_item(self, item: Dict[str, Any], current: int, total: int):
        # Check if already in records by channel_url
        found = False
        for idx, existing in enumerate(self.records):
            if existing.get("channel_url") == item.get("channel_url"):
                self.records[idx].update(item)
                found = True
                break
        if not found:
            self.records.append(item)

        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = min(current, total)
        self._refresh_table()

    # -------------------------------------------------------------
    # Table & Data Management
    # -------------------------------------------------------------
    def _refresh_table(self):
        query = self.filter_var.get().strip().lower()
        min_sub_sel = self.min_sub_combo.get().strip()
        min_sub_val = 0
        if min_sub_sel and min_sub_sel != "Any":
            clean_digits = re.sub(r'[^\d]', '', min_sub_sel)
            if clean_digits:
                min_sub_val = int(clean_digits)

        self.tree.delete(*self.tree.get_children())

        displayed = 0
        for i, item in enumerate(self.records, 1):
            # Check subscriber filter
            if min_sub_val > 0:
                sc = item.get("subscribers_count", 0)
                if sc < min_sub_val:
                    continue

            # Check text query
            if query:
                combined = " ".join([
                    str(item.get("name", "")),
                    str(item.get("handle", "")),
                    str(item.get("contact", "")),
                    str(item.get("website", "")),
                    str(item.get("video_title", "")),
                    str(item.get("description", ""))
                ]).lower()
                if query not in combined:
                    continue

            tag = "evenrow" if displayed % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                iid=str(i - 1),
                values=(
                    i,
                    item.get("name", ""),
                    item.get("handle", ""),
                    item.get("subscribers", ""),
                    item.get("videos_count", ""),
                    item.get("contact", ""),
                    item.get("website", ""),
                    item.get("video_title", ""),
                    item.get("channel_url", "")
                ),
                tags=(tag,)
            )
            displayed += 1

        self._update_stats(displayed)

    def _apply_filters(self):
        self._refresh_table()

    def _update_stats(self, displayed_count: Optional[int] = None):
        total = len(self.records)
        if displayed_count is None:
            displayed_count = len(self.tree.get_children())
        if displayed_count < total:
            self.stats_lbl.config(text=f"Showing: {displayed_count} of {total} channels")
        else:
            self.stats_lbl.config(text=f"Total Channels: {total}")

    def _sort_column(self, col: str, reverse: bool):
        items = []
        for k in self.tree.get_children(""):
            val = self.tree.set(k, col)
            if col == "subscribers":
                idx = int(k)
                if idx < len(self.records):
                    num_val = self.records[idx].get("subscribers_count", 0)
                    items.append((num_val, k))
                else:
                    items.append((0, k))
            else:
                items.append((val, k))

        try:
            items.sort(key=lambda t: float(str(t[0]).replace(",", "") or 0), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(items):
            self.tree.move(k, "", index)
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.item(k, tags=(tag,))

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    # -------------------------------------------------------------
    # Record Editing & Context Actions
    # -------------------------------------------------------------
    def _edit_selected_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please select a channel from the table to edit.")
            return

        record_idx = int(selected[0])
        if record_idx < 0 or record_idx >= len(self.records):
            return

        record = self.records[record_idx]

        def on_save_callback(updated_data):
            self.records[record_idx].update(updated_data)
            self._refresh_table()
            self.status_lbl.config(text=f"Updated channel: {updated_data.get('name')}")

        EditChannelDialog(self.root, item_data=record, on_save=on_save_callback)

    def _add_new_record(self):
        def on_add_callback(new_data):
            self.records.append(new_data)
            self._refresh_table()
            self.status_lbl.config(text=f"Added new channel: {new_data.get('name')}")

        EditChannelDialog(self.root, item_data=None, on_save=on_add_callback)

    def _delete_selected_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please select one or more channels to delete.")
            return

        count = len(selected)
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {count} selected channel(s)?",
            icon="warning"
        )
        if not confirm:
            return

        indices_to_remove = sorted([int(iid) for iid in selected], reverse=True)
        for idx in indices_to_remove:
            if 0 <= idx < len(self.records):
                self.records.pop(idx)

        self._refresh_table()
        self.status_lbl.config(text=f"Deleted {count} record(s).")

    def _clear_all_records(self):
        if not self.records:
            return
        confirm = messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all records from the table?", icon="warning")
        if confirm:
            self.records.clear()
            self._refresh_table()
            self.status_lbl.config(text="All records cleared.")

    def _open_channel(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        url = self.records[idx].get("channel_url")
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("No URL", "No channel URL available.")

    def _open_video(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        url = self.records[idx].get("video_url")
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("No Video", "No source video URL recorded for this channel.")

    def _open_website(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        url = self.records[idx].get("website")
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("No Website", "No external website URL available.")

    def _copy_contact(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        contact = self.records[idx].get("contact", "")
        if contact:
            self.root.clipboard_clear()
            self.root.clipboard_append(contact)
            self.status_lbl.config(text=f"Copied contact to clipboard: {contact}")
        else:
            messagebox.showinfo("No Contact", "No contact/email found for this channel.")

    def _copy_channel_link(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        url = self.records[idx].get("channel_url", "")
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.status_lbl.config(text="Copied channel link to clipboard.")

    # -------------------------------------------------------------
    # Exporting with Custom Column Selection
    # -------------------------------------------------------------
    def _export_csv(self):
        if not self.records:
            messagebox.showwarning("No Data", "There are no listings to export. Please scrape or add records first.")
            return

        cols = [
            "Index", "Channel Name", "Handle", "Subscribers", "Videos Count",
            "Contact / Email", "Website / Links", "Source Video Title",
            "Source Video URL", "Channel URL", "Description"
        ]

        def on_columns_chosen(selected_cols):
            default_name = f"youtube_{self._sanitize_filename(self.current_query or 'results')}.csv"
            filepath = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export YouTube Data to CSV",
                initialfile=default_name,
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if not filepath:
                return

            try:
                export_to_csv(self.records, filepath, selected_columns=selected_cols)
                messagebox.showinfo("Export Successful", f"Successfully exported {len(self.records)} channels ({len(selected_cols)} columns) to:\n{filepath}")
                self.status_lbl.config(text=f"Exported to CSV ({len(selected_cols)} cols): {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export CSV:\n{e}")

        ColumnSelectorDialog(self.root, cols, on_columns_chosen, title="Select Columns for CSV Export")

    def _export_txt(self):
        if not self.records:
            messagebox.showwarning("No Data", "There are no listings to export. Please scrape or add records first.")
            return

        cols = [
            "Channel Name", "Handle", "Subscribers", "Videos Count",
            "Contact / Email", "Website / Links", "Source Video Title",
            "Source Video URL", "Channel URL", "Description"
        ]

        def on_columns_chosen(selected_cols):
            default_name = f"youtube_{self._sanitize_filename(self.current_query or 'results')}.txt"
            filepath = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export YouTube Data to TXT Report",
                initialfile=default_name,
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not filepath:
                return

            try:
                export_to_txt(self.records, filepath, keyword=self.current_query, selected_columns=selected_cols)
                messagebox.showinfo("Export Successful", f"Successfully exported {len(self.records)} channels to:\n{filepath}")
                self.status_lbl.config(text=f"Exported to TXT ({len(selected_cols)} cols): {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export TXT:\n{e}")

        ColumnSelectorDialog(self.root, cols, on_columns_chosen, title="Select Columns for TXT Export")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in name).strip().replace(" ", "_")


def main():
    root = tk.Tk()
    app = YouTubeDataScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
