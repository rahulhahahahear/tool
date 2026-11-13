"""
Google Maps Scraper - Interactive GUI Application (scan_from_map module)
Allows searching, scraping, live table listing, inline editing, and exporting to CSV/TXT.
"""

import sys
import os
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional

try:
    from .scraper import GoogleMapsScraper
    from .exporter import export_to_csv, export_to_txt
except (ImportError, ValueError):
    from scraper import GoogleMapsScraper
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


class EditBusinessDialog(tk.Toplevel):
    """Modal dialog to edit or create a business record."""

    def __init__(self, parent, item_data: Optional[Dict[str, Any]] = None, on_save=None):
        super().__init__(parent)
        self.item_data = item_data or {}
        self.on_save = on_save
        self.saved = False

        self.title("Edit Business Details" if item_data else "Add New Business")
        self.geometry("560x620")
        self.minsize(480, 520)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._populate_fields()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            main_frame,
            text="Edit Business Information" if self.item_data else "Add Business Information",
            font=("Segoe UI", 12, "bold")
        )
        header.pack(anchor="w", pady=(0, 15))

        # Fields container
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        self.entries = {}
        fields = [
            ("name", "Business Name *"),
            ("phone", "Phone Number"),
            ("website", "Website URL"),
            ("rating", "Rating (e.g. 4.5)"),
            ("reviews", "Review Count"),
            ("category", "Category / Type"),
            ("address", "Full Address"),
            ("hours", "Opening Hours / Status"),
            ("url", "Google Maps URL"),
            ("notes", "Notes / Lead Remarks"),
        ]

        for i, (key, label) in enumerate(fields):
            lbl = ttk.Label(form_frame, text=label, font=("Segoe UI", 9))
            lbl.grid(row=i, column=0, sticky="w", pady=4, padx=(0, 10))

            entry = ttk.Entry(form_frame, font=("Segoe UI", 9))
            entry.grid(row=i, column=1, sticky="ew", pady=4)
            self.entries[key] = entry

        form_frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
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
            messagebox.showwarning("Validation Error", "Business Name is required.", parent=self)
            return

        updated_data = {key: self.entries[key].get().strip() for key in self.entries}
        self.saved = True
        if self.on_save:
            self.on_save(updated_data)
        self.destroy()


class GoogleMapsScraperApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Scan From Map - Google Maps Scraper & Editor")
        self.root.geometry("1180x720")
        self.root.minsize(900, 550)

        # Dataset storage
        self.records: List[Dict[str, Any]] = []
        self.active_scraper: Optional[GoogleMapsScraper] = None
        self.is_scraping = False
        self.current_query = ""

        # Setup custom modern theme styles
        self._setup_styles()

        # Build UI layout
        self._build_top_search_panel()
        self._build_filter_and_stats_panel()
        self._build_table_panel()
        self._build_bottom_toolbar()
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
            background="#2563eb",
            padding=6
        )
        self.style.map("Accent.TButton", background=[("active", "#1d4ed8"), ("disabled", "#94a3b8")])

        self.style.configure(
            "Stop.TButton",
            font=("Segoe UI", 9, "bold"),
            foreground="#ffffff",
            background="#dc2626",
            padding=6
        )
        self.style.map("Stop.TButton", background=[("active", "#b91c1c"), ("disabled", "#fca5a5")])

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
        self.style.map("Treeview", background=[("selected", "#3b82f6")], foreground=[("selected", "#ffffff")])

    def _build_top_search_panel(self):
        container = ttk.LabelFrame(self.root, text="Search & Scrape Settings", padding="12")
        container.pack(fill=tk.X, padx=12, pady=(10, 6))

        r1 = ttk.Frame(container)
        r1.pack(fill=tk.X)

        ttk.Label(r1, text="Keyword / Query:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.keyword_entry = ttk.Entry(r1, font=("Segoe UI", 10), width=34)
        self.keyword_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.keyword_entry.insert(0, "cafes in new york")
        self.keyword_entry.bind("<Return>", lambda e: self._start_scraping())

        ttk.Label(r1, text="Results Limit:").pack(side=tk.LEFT, padx=(0, 5))
        self.limit_combo = ttk.Combobox(r1, values=["10", "20", "50", "100", "200"], width=6, state="readonly")
        self.limit_combo.set("20")
        self.limit_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(r1, text="Browser:").pack(side=tk.LEFT, padx=(0, 5))
        self.browser_combo = ttk.Combobox(r1, values=["chrome", "msedge"], width=8, state="readonly")
        self.browser_combo.set("chrome")
        self.browser_combo.pack(side=tk.LEFT, padx=(0, 15))

        self.headless_var = tk.BooleanVar(value=True)
        self.headless_cb = ttk.Checkbutton(r1, text="Headless (Invisible Browser)", variable=self.headless_var)
        self.headless_cb.pack(side=tk.LEFT, padx=(0, 15))

        self.start_btn = ttk.Button(r1, text="🔍 Scrape Google Maps", command=self._start_scraping, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = ttk.Button(r1, text="⏹ Stop", command=self._stop_scraping, style="Stop.TButton", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

    def _build_filter_and_stats_panel(self):
        container = ttk.Frame(self.root, padding="12 4")
        container.pack(fill=tk.X)

        ttk.Label(container, text="🔎 Quick Filter:").pack(side=tk.LEFT, padx=(0, 6))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *args: self._apply_filter())
        self.filter_entry = ttk.Entry(container, textvariable=self.filter_var, font=("Segoe UI", 9), width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 15))

        self.stats_lbl = ttk.Label(container, text="Total Listings: 0", font=("Segoe UI", 9, "bold"), foreground="#2563eb")
        self.stats_lbl.pack(side=tk.RIGHT)

        hint_lbl = ttk.Label(container, text="(Double-click any row to edit)", style="Muted.TLabel")
        hint_lbl.pack(side=tk.RIGHT, padx=15)

    def _build_table_panel(self):
        table_frame = ttk.Frame(self.root, padding="12 0")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("idx", "name", "phone", "website", "rating", "reviews", "category", "address", "hours")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        headings = [
            ("idx", "#", 45, "center"),
            ("name", "Business Name", 220, "w"),
            ("phone", "Phone", 130, "w"),
            ("website", "Website", 180, "w"),
            ("rating", "Rating", 60, "center"),
            ("reviews", "Reviews", 70, "center"),
            ("category", "Category", 130, "w"),
            ("address", "Address", 240, "w"),
            ("hours", "Hours / Status", 150, "w"),
        ]

        for col, title, width, anchor in headings:
            self.tree.heading(col, text=title, command=lambda c=col: self._sort_column(c, False))
            self.tree.column(col, width=width, anchor=anchor, stretch=(col in ("name", "address", "website")))

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
        self.context_menu.add_command(label="✏️ Edit Listing...", command=self._edit_selected_record)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🌐 Open Website", command=self._open_website)
        self.context_menu.add_command(label="🗺️ View on Google Maps", command=self._open_gmaps)
        self.context_menu.add_command(label="📋 Copy Phone Number", command=self._copy_phone)
        self.context_menu.add_command(label="📋 Copy Address", command=self._copy_address)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ Delete Selected", command=self._delete_selected_record)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _build_bottom_toolbar(self):
        toolbar = ttk.Frame(self.root, padding="12 8")
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="✏️ Edit Selected", command=self._edit_selected_record).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="➕ Add Business", command=self._add_new_record).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🗑️ Delete Selected", command=self._delete_selected_record).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🧹 Clear All", command=self._clear_all_records).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="💾 Export to CSV", command=self._export_csv, style="Accent.TButton").pack(side=tk.RIGHT, padx=4)
        ttk.Button(toolbar, text="📄 Export to TXT", command=self._export_txt).pack(side=tk.RIGHT, padx=4)

    def _build_status_bar(self):
        bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding="6 4")
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_bar = ttk.Progressbar(bar, orient=tk.HORIZONTAL, mode="determinate", length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 5))

        self.status_lbl = ttk.Label(bar, text="Ready. Enter a keyword to start scraping Google Maps.", anchor="w")
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
            limit = 20

        self.current_query = keyword
        browser_choice = self.browser_combo.get()
        headless_choice = self.headless_var.get()

        self.is_scraping = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = limit
        self.status_lbl.config(text=f"Initializing scraper for '{keyword}'...")

        self.active_scraper = GoogleMapsScraper(
            headless=headless_choice,
            preferred_channel=browser_choice,
            on_progress=self._thread_on_progress,
            on_item_scraped=self._thread_on_item_scraped
        )

        threading.Thread(target=self._run_scraper_worker, args=(keyword, limit), daemon=True).start()

    def _stop_scraping(self):
        if self.active_scraper and self.is_scraping:
            self.status_lbl.config(text="Sending stop signal to scraper...")
            self.active_scraper.request_stop()
            self.stop_btn.configure(state=tk.DISABLED)

    def _run_scraper_worker(self, keyword: str, limit: int):
        try:
            self.active_scraper.scrape(keyword, max_results=limit)
        except Exception as e:
            self.root.after(0, self._thread_on_error, str(e))
        finally:
            self.root.after(0, self._thread_on_finish)

    def _thread_on_progress(self, msg: str):
        self.root.after(0, self._update_status, msg)

    def _thread_on_item_scraped(self, item: Dict[str, Any], current: int, total: int):
        self.root.after(0, self._add_scraped_item, item, current, total)

    def _thread_on_error(self, err_msg: str):
        messagebox.showerror("Scraping Error", f"An error occurred while scraping:\n{err_msg}")

    def _thread_on_finish(self):
        self.is_scraping = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress_bar["value"] = self.progress_bar["maximum"]
        self.status_lbl.config(text=f"Scraping finished. Total listings in database: {len(self.records)}")
        self._update_stats()

    def _update_status(self, msg: str):
        self.status_lbl.config(text=msg)

    def _add_scraped_item(self, item: Dict[str, Any], current: int, total: int):
        self.records.append(item)
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current
        self._refresh_table()

    # -------------------------------------------------------------
    # Table & Data Management
    # -------------------------------------------------------------
    def _refresh_table(self):
        query = self.filter_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        displayed = 0
        for i, item in enumerate(self.records, 1):
            if query:
                combined = " ".join([
                    str(item.get("name", "")),
                    str(item.get("phone", "")),
                    str(item.get("website", "")),
                    str(item.get("category", "")),
                    str(item.get("address", "")),
                    str(item.get("hours", ""))
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
                    item.get("phone", ""),
                    item.get("website", ""),
                    item.get("rating", ""),
                    item.get("reviews", ""),
                    item.get("category", ""),
                    item.get("address", ""),
                    item.get("hours", "")
                ),
                tags=(tag,)
            )
            displayed += 1

        self._update_stats(displayed)

    def _apply_filter(self):
        self._refresh_table()

    def _update_stats(self, displayed_count: Optional[int] = None):
        total = len(self.records)
        if displayed_count is None:
            displayed_count = len(self.tree.get_children())
        if displayed_count < total:
            self.stats_lbl.config(text=f"Showing: {displayed_count} of {total} listings")
        else:
            self.stats_lbl.config(text=f"Total Listings: {total}")

    def _sort_column(self, col: str, reverse: bool):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            items.sort(key=lambda t: float(t[0].replace(",", "") or 0), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(items):
            self.tree.move(k, "", index)
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.item(k, tags=(tag,))

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    # -------------------------------------------------------------
    # Record Editing & Actions
    # -------------------------------------------------------------
    def _edit_selected_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please select a business listing from the table to edit.")
            return

        item_id = selected[0]
        record_idx = int(item_id)
        if record_idx < 0 or record_idx >= len(self.records):
            return

        record = self.records[record_idx]

        def on_save_callback(updated_data):
            self.records[record_idx].update(updated_data)
            self._refresh_table()
            self.status_lbl.config(text=f"Updated listing: {updated_data.get('name')}")

        EditBusinessDialog(self.root, item_data=record, on_save=on_save_callback)

    def _add_new_record(self):
        def on_add_callback(new_data):
            self.records.append(new_data)
            self._refresh_table()
            self.status_lbl.config(text=f"Added new listing: {new_data.get('name')}")

        EditBusinessDialog(self.root, item_data=None, on_save=on_add_callback)

    def _delete_selected_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please select one or more listings to delete.")
            return

        count = len(selected)
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {count} selected listing(s)?",
            icon="warning"
        )
        if not confirm:
            return

        indices_to_remove = sorted([int(iid) for iid in selected], reverse=True)
        for idx in indices_to_remove:
            if 0 <= idx < len(self.records):
                self.records.pop(idx)

        self._refresh_table()
        self.status_lbl.config(text=f"Deleted {count} listing(s).")

    def _clear_all_records(self):
        if not self.records:
            return
        confirm = messagebox.askyesno(
            "Confirm Clear All",
            "Are you sure you want to clear all listings from the table?",
            icon="warning"
        )
        if confirm:
            self.records.clear()
            self._refresh_table()
            self.status_lbl.config(text="All listings cleared.")

    def _open_website(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        url = self.records[idx].get("website")
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("No Website", "No website URL available for this listing.")

    def _open_gmaps(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        url = self.records[idx].get("url")
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("No Maps URL", "No Google Maps URL available.")

    def _copy_phone(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        phone = self.records[idx].get("phone", "")
        if phone:
            self.root.clipboard_clear()
            self.root.clipboard_append(phone)
            self.status_lbl.config(text=f"Copied phone to clipboard: {phone}")

    def _copy_address(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        addr = self.records[idx].get("address", "")
        if addr:
            self.root.clipboard_clear()
            self.root.clipboard_append(addr)
            self.status_lbl.config(text="Copied address to clipboard.")

    # -------------------------------------------------------------
    # Exporting
    # -------------------------------------------------------------
    def _export_csv(self):
        if not self.records:
            messagebox.showwarning("No Data", "There are no listings to export. Please scrape or add records first.")
            return

        cols = ["Index", "Name", "Phone", "Website", "Rating", "Reviews", "Category", "Address", "Hours", "Google Maps URL", "Notes"]

        def on_columns_chosen(selected_cols):
            default_name = f"google_maps_{self._sanitize_filename(self.current_query or 'results')}.csv"
            filepath = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export Records to CSV",
                initialfile=default_name,
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if not filepath:
                return

            try:
                export_to_csv(self.records, filepath, selected_columns=selected_cols)
                messagebox.showinfo("Export Successful", f"Successfully exported {len(self.records)} listings ({len(selected_cols)} columns) to:\n{filepath}")
                self.status_lbl.config(text=f"Exported to CSV ({len(selected_cols)} cols): {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export CSV:\n{e}")

        ColumnSelectorDialog(self.root, cols, on_columns_chosen, title="Select Columns for CSV Export")

    def _export_txt(self):
        if not self.records:
            messagebox.showwarning("No Data", "There are no listings to export. Please scrape or add records first.")
            return

        cols = ["Name", "Phone", "Website", "Rating", "Category", "Address", "Hours", "Google Maps URL", "Notes"]

        def on_columns_chosen(selected_cols):
            default_name = f"google_maps_{self._sanitize_filename(self.current_query or 'results')}.txt"
            filepath = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export Records to TXT Report",
                initialfile=default_name,
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not filepath:
                return

            try:
                export_to_txt(self.records, filepath, keyword=self.current_query, selected_columns=selected_cols)
                messagebox.showinfo("Export Successful", f"Successfully exported {len(self.records)} listings to:\n{filepath}")
                self.status_lbl.config(text=f"Exported to TXT ({len(selected_cols)} cols): {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export TXT:\n{e}")

        ColumnSelectorDialog(self.root, cols, on_columns_chosen, title="Select Columns for TXT Export")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in name).strip().replace(" ", "_")


def main():
    root = tk.Tk()
    app = GoogleMapsScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
