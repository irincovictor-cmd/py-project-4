"""
School Library and Textbook Management System
Simple offline prototype using Python + Tkinter.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import date, timedelta
from PIL import Image, ImageTk
import shutil

import storage


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Library and Textbook Management System")
        self.root.geometry("1000x650")
        self.root.minsize(900, 600)

        # Load data
        self.data = storage.load_data()
        storage.update_overdue_statuses(self.data)

        # Image cache
        self.photo_cache = {}

        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Style
        style = ttk.Style()
        style.theme_use("clam")

        # Top frame - title and status
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(
            top,
            text="School Library & Textbook Management System",
            font=("Segoe UI", 16, "bold")
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar()
        ttk.Label(top, textvariable=self.status_var, font=("Segoe UI", 10)).pack(side=tk.RIGHT)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # ---- Tab 1: Inventory ----
        self.tab_inventory = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_inventory, text="  Book Inventory  ")
        self._build_inventory_tab()

        # ---- Tab 2: Borrow ----
        self.tab_borrow = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_borrow, text="  Borrow Book  ")
        self._build_borrow_tab()

        # ---- Tab 3: Return ----
        self.tab_return = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_return, text="  Return Book  ")
        self._build_return_tab()

        # ---- Tab 4: Reports ----
        self.tab_reports = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_reports, text="  Reports  ")
        self._build_reports_tab()

    def _build_inventory_tab(self):
        # Search bar
        search_frame = ttk.Frame(self.tab_inventory)
        search_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(search_frame, text="Search (Title / Author):").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_inventory())
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side=tk.LEFT, padx=6)

        ttk.Button(search_frame, text="Refresh", command=self.refresh_all).pack(side=tk.RIGHT)

        # Main content: list + form
        content = ttk.Frame(self.tab_inventory)
        content.pack(fill=tk.BOTH, expand=True)

        # Left: book list
        left = ttk.Frame(content)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("book_id", "title", "author", "category", "available", "total")
        self.tree_books = ttk.Treeview(left, columns=columns, show="headings", height=18)
        self.tree_books.heading("book_id", text="ID")
        self.tree_books.heading("title", text="Title")
        self.tree_books.heading("author", text="Author")
        self.tree_books.heading("category", text="Category")
        self.tree_books.heading("available", text="Available")
        self.tree_books.heading("total", text="Total")

        self.tree_books.column("book_id", width=70, anchor=tk.CENTER)
        self.tree_books.column("title", width=200)
        self.tree_books.column("author", width=120)
        self.tree_books.column("category", width=100)
        self.tree_books.column("available", width=80, anchor=tk.CENTER)
        self.tree_books.column("total", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree_books.yview)
        self.tree_books.configure(yscrollcommand=scrollbar.set)
        self.tree_books.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_books.bind("<<TreeviewSelect>>", self.on_book_select)

        # Right: form + image + buttons
        right = ttk.Frame(content, padding=(12, 0, 0, 0))
        right.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(right, text="Book Details", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)

        form = ttk.Frame(right)
        form.pack(fill=tk.X, pady=6)

        labels = ["Title:", "Author:", "Category:", "Total Copies:"]
        self.form_vars = {
            "title": tk.StringVar(),
            "author": tk.StringVar(),
            "category": tk.StringVar(),
            "total": tk.StringVar(),
        }

        for i, (label, key) in enumerate(zip(labels, self.form_vars.keys())):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            ttk.Entry(form, textvariable=self.form_vars[key], width=28).grid(row=i, column=1, pady=3, padx=4)

        # Image preview
        self.img_label = ttk.Label(right, text="No Image", relief=tk.SUNKEN, width=25)
        self.img_label.pack(pady=8)

        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X, pady=4)

        ttk.Button(btn_frame, text="Add New Book", command=self.add_book).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_book).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_book).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Choose Cover Image", command=self.choose_image).pack(fill=tk.X, pady=2)

        self.selected_book_id = None
        self.selected_image_path = None

    def _build_borrow_tab(self):
        # Available books list
        ttk.Label(self.tab_borrow, text="Available Books", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)

        columns = ("book_id", "title", "author", "available")
        self.tree_available = ttk.Treeview(self.tab_borrow, columns=columns, show="headings", height=12)
        for col, text, w in zip(columns, ["ID", "Title", "Author", "Available"], [70, 250, 150, 80]):
            self.tree_available.heading(col, text=text)
            self.tree_available.column(col, width=w, anchor=tk.CENTER if col != "title" else tk.W)
        self.tree_available.pack(fill=tk.BOTH, expand=True, pady=4)

        # Borrow form
        form = ttk.LabelFrame(self.tab_borrow, text="Borrow Details", padding=10)
        form.pack(fill=tk.X, pady=8)

        ttk.Label(form, text="Borrower Name:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.borrower_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.borrower_var, width=35).grid(row=0, column=1, pady=4, padx=6)

        ttk.Label(form, text="Due Date (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.due_var = tk.StringVar(value=(date.today() + timedelta(days=14)).isoformat())
        ttk.Entry(form, textvariable=self.due_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=4, padx=6)

        ttk.Button(form, text="Borrow Selected Book", command=self.borrow_book).grid(row=2, column=0, columnspan=2, pady=8)

    def _build_return_tab(self):
        ttk.Label(self.tab_return, text="Currently Borrowed / Overdue Books", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)

        columns = ("record_id", "book_id", "title", "borrower", "borrow_date", "due_date", "status")
        self.tree_borrowed = ttk.Treeview(self.tab_return, columns=columns, show="headings", height=16)
        headers = ["Record", "Book ID", "Title", "Borrower", "Borrowed", "Due Date", "Status"]
        widths = [70, 70, 180, 140, 90, 90, 80]
        for col, text, w in zip(columns, headers, widths):
            self.tree_borrowed.heading(col, text=text)
            self.tree_borrowed.column(col, width=w, anchor=tk.CENTER if col != "title" and col != "borrower" else tk.W)
        self.tree_borrowed.pack(fill=tk.BOTH, expand=True, pady=4)

        btn_frame = ttk.Frame(self.tab_return)
        btn_frame.pack(fill=tk.X, pady=6)
        ttk.Button(btn_frame, text="Return Selected Book", command=self.return_book).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Refresh List", command=self.refresh_return).pack(side=tk.LEFT, padx=4)

    def _build_reports_tab(self):
        # Buttons to switch report type
        btn_frame = ttk.Frame(self.tab_reports)
        btn_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Button(btn_frame, text="Currently Borrowed", command=lambda: self.show_report("borrowed")).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Overdue Books", command=lambda: self.show_report("overdue")).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Available Books Summary", command=lambda: self.show_report("available")).pack(side=tk.LEFT, padx=3)

        self.report_text = tk.Text(self.tab_reports, height=25, wrap=tk.WORD, font=("Consolas", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        self.report_text.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------
    def refresh_all(self):
        storage.update_overdue_statuses(self.data)
        self.refresh_inventory()
        self.refresh_available()
        self.refresh_return()
        self.update_status()
        self.show_report("borrowed")

    def update_status(self):
        total_books = len(self.data["books"])
        total_copies = sum(b["total_copies"] for b in self.data["books"])
        available = sum(b["available_copies"] for b in self.data["books"])
        overdue = sum(1 for r in self.data["records"] if r.get("status") == "Overdue")
        self.status_var.set(f"Books: {total_books}  |  Copies: {available}/{total_copies} available  |  Overdue: {overdue}")

    def refresh_inventory(self):
        for item in self.tree_books.get_children():
            self.tree_books.delete(item)

        query = self.search_var.get().strip().lower()
        for book in self.data["books"]:
            if query:
                if query not in book["title"].lower() and query not in book["author"].lower():
                    continue
            self.tree_books.insert("", tk.END, values=(
                book["book_id"],
                book["title"],
                book["author"],
                book["category"],
                book["available_copies"],
                book["total_copies"]
            ))

    def refresh_available(self):
        for item in self.tree_available.get_children():
            self.tree_available.delete(item)
        for book in self.data["books"]:
            if book["available_copies"] > 0:
                self.tree_available.insert("", tk.END, values=(
                    book["book_id"],
                    book["title"],
                    book["author"],
                    book["available_copies"]
                ))

    def refresh_return(self):
        for item in self.tree_borrowed.get_children():
            self.tree_borrowed.delete(item)

        # Build title lookup
        titles = {b["book_id"]: b["title"] for b in self.data["books"]}

        for rec in self.data["records"]:
            if rec.get("status") in ("Borrowed", "Overdue"):
                self.tree_borrowed.insert("", tk.END, values=(
                    rec["record_id"],
                    rec["book_id"],
                    titles.get(rec["book_id"], "Unknown"),
                    rec["borrower_name"],
                    rec["borrow_date"],
                    rec["due_date"],
                    rec["status"]
                ))

    # ------------------------------------------------------------------
    # Inventory actions
    # ------------------------------------------------------------------
    def on_book_select(self, event=None):
        selected = self.tree_books.selection()
        if not selected:
            return
        values = self.tree_books.item(selected[0], "values")
        book_id = values[0]
        book = next((b for b in self.data["books"] if b["book_id"] == book_id), None)
        if not book:
            return

        self.selected_book_id = book_id
        self.form_vars["title"].set(book["title"])
        self.form_vars["author"].set(book["author"])
        self.form_vars["category"].set(book["category"])
        self.form_vars["total"].set(str(book["total_copies"]))
        self.selected_image_path = None
        self.show_cover(book.get("image"))

    def show_cover(self, image_name):
        self.img_label.configure(image="", text="No Image")
        if not image_name:
            return
        path = os.path.join(storage.get_images_dir(), image_name)
        if not os.path.exists(path):
            return
        try:
            img = Image.open(path)
            img.thumbnail((140, 180))
            photo = ImageTk.PhotoImage(img)
            self.photo_cache["preview"] = photo  # keep reference
            self.img_label.configure(image=photo, text="")
        except Exception:
            self.img_label.configure(text="Image Error")

    def clear_form(self):
        self.selected_book_id = None
        self.selected_image_path = None
        for var in self.form_vars.values():
            var.set("")
        self.img_label.configure(image="", text="No Image")
        self.tree_books.selection_remove(self.tree_books.selection())

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if path:
            self.selected_image_path = path
            try:
                img = Image.open(path)
                img.thumbnail((140, 180))
                photo = ImageTk.PhotoImage(img)
                self.photo_cache["preview"] = photo
                self.img_label.configure(image=photo, text="")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open image:\n{e}")

    def add_book(self):
        title = self.form_vars["title"].get().strip()
        author = self.form_vars["author"].get().strip()
        category = self.form_vars["category"].get().strip()
        total_str = self.form_vars["total"].get().strip()

        if not title or not author:
            messagebox.showwarning("Validation", "Title and Author are required.")
            return
        try:
            total = int(total_str)
            if total < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation", "Total Copies must be a positive whole number.")
            return

        book_id = storage.generate_book_id(self.data)
        image_name = ""

        if self.selected_image_path:
            ext = os.path.splitext(self.selected_image_path)[1].lower() or ".png"
            image_name = f"{book_id}{ext}"
            dest = os.path.join(storage.get_images_dir(), image_name)
            try:
                shutil.copy2(self.selected_image_path, dest)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy image:\n{e}")
                return

        new_book = {
            "book_id": book_id,
            "title": title,
            "author": author,
            "category": category or "General",
            "total_copies": total,
            "available_copies": total,
            "image": image_name
        }
        self.data["books"].append(new_book)
        storage.save_data(self.data)
        self.clear_form()
        self.refresh_all()
        messagebox.showinfo("Success", f"Book '{title}' added with ID {book_id}.")

    def update_book(self):
        if not self.selected_book_id:
            messagebox.showwarning("Selection", "Please select a book first.")
            return

        book = next((b for b in self.data["books"] if b["book_id"] == self.selected_book_id), None)
        if not book:
            return

        title = self.form_vars["title"].get().strip()
        author = self.form_vars["author"].get().strip()
        category = self.form_vars["category"].get().strip()
        total_str = self.form_vars["total"].get().strip()

        if not title or not author:
            messagebox.showwarning("Validation", "Title and Author are required.")
            return
        try:
            total = int(total_str)
            if total < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation", "Total Copies must be a positive whole number.")
            return

        # Adjust available if total changed
        borrowed = book["total_copies"] - book["available_copies"]
        if total < borrowed:
            messagebox.showwarning("Validation", f"Cannot set total copies below currently borrowed ({borrowed}).")
            return

        book["title"] = title
        book["author"] = author
        book["category"] = category or "General"
        book["total_copies"] = total
        book["available_copies"] = total - borrowed

        if self.selected_image_path:
            ext = os.path.splitext(self.selected_image_path)[1].lower() or ".png"
            image_name = f"{book['book_id']}{ext}"
            dest = os.path.join(storage.get_images_dir(), image_name)
            try:
                shutil.copy2(self.selected_image_path, dest)
                book["image"] = image_name
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy image:\n{e}")
                return

        storage.save_data(self.data)
        self.clear_form()
        self.refresh_all()
        messagebox.showinfo("Success", "Book updated successfully.")

    def delete_book(self):
        if not self.selected_book_id:
            messagebox.showwarning("Selection", "Please select a book first.")
            return

        book = next((b for b in self.data["books"] if b["book_id"] == self.selected_book_id), None)
        if not book:
            return

        # Check if any active borrow
        active = any(r["book_id"] == book["book_id"] and r["status"] in ("Borrowed", "Overdue")
                     for r in self.data["records"])
        if active:
            messagebox.showwarning("Cannot Delete", "This book has active borrow records. Return them first.")
            return

        if not messagebox.askyesno("Confirm Delete", f"Delete '{book['title']}'?\nThis cannot be undone."):
            return

        self.data["books"] = [b for b in self.data["books"] if b["book_id"] != self.selected_book_id]
        storage.save_data(self.data)
        self.clear_form()
        self.refresh_all()
        messagebox.showinfo("Deleted", "Book removed from inventory.")

    # ------------------------------------------------------------------
    # Borrow / Return
    # ------------------------------------------------------------------
    def borrow_book(self):
        selected = self.tree_available.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a book to borrow.")
            return

        values = self.tree_available.item(selected[0], "values")
        book_id = values[0]
        book = next((b for b in self.data["books"] if b["book_id"] == book_id), None)
        if not book or book["available_copies"] < 1:
            messagebox.showwarning("Unavailable", "This book is no longer available.")
            self.refresh_available()
            return

        borrower = self.borrower_var.get().strip()
        if not borrower:
            messagebox.showwarning("Validation", "Borrower name is required.")
            return

        due_str = self.due_var.get().strip()
        due_date = storage.parse_date(due_str)
        if due_date is None:
            messagebox.showwarning("Validation", "Due date must be in YYYY-MM-DD format.")
            return
        if due_date < date.today():
            messagebox.showwarning("Validation", "Due date cannot be in the past.")
            return

        # Create record
        record = {
            "record_id": storage.generate_record_id(self.data),
            "book_id": book_id,
            "borrower_name": borrower,
            "borrow_date": storage.today_str(),
            "due_date": due_str,
            "return_date": None,
            "status": "Borrowed"
        }
        self.data["records"].append(record)
        book["available_copies"] -= 1
        storage.save_data(self.data)

        self.borrower_var.set("")
        self.due_var.set((date.today() + timedelta(days=14)).isoformat())
        self.refresh_all()
        messagebox.showinfo("Success", f"'{book['title']}' borrowed by {borrower}.\nDue: {due_str}")

    def return_book(self):
        selected = self.tree_borrowed.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a record to return.")
            return

        values = self.tree_borrowed.item(selected[0], "values")
        record_id = values[0]
        record = next((r for r in self.data["records"] if r["record_id"] == record_id), None)
        if not record or record["status"] not in ("Borrowed", "Overdue"):
            messagebox.showwarning("Invalid", "This record is not active.")
            return

        book = next((b for b in self.data["books"] if b["book_id"] == record["book_id"]), None)

        if not messagebox.askyesno("Confirm Return", f"Return book borrowed by {record['borrower_name']}?"):
            return

        record["status"] = "Returned"
        record["return_date"] = storage.today_str()
        if book:
            book["available_copies"] += 1
            # Safety
            if book["available_copies"] > book["total_copies"]:
                book["available_copies"] = book["total_copies"]

        storage.save_data(self.data)
        self.refresh_all()
        messagebox.showinfo("Returned", "Book has been returned successfully.")

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def show_report(self, report_type):
        self.report_text.configure(state=tk.NORMAL)
        self.report_text.delete("1.0", tk.END)

        titles = {b["book_id"]: b["title"] for b in self.data["books"]}

        if report_type == "borrowed":
            lines = ["CURRENTLY BORROWED BOOKS", "=" * 50, ""]
            active = [r for r in self.data["records"] if r["status"] in ("Borrowed", "Overdue")]
            if not active:
                lines.append("No books are currently borrowed.")
            else:
                for r in active:
                    lines.append(f"{r['record_id']}  |  {r['book_id']} - {titles.get(r['book_id'], '?')}")
                    lines.append(f"   Borrower : {r['borrower_name']}")
                    lines.append(f"   Borrowed : {r['borrow_date']}   Due: {r['due_date']}   Status: {r['status']}")
                    lines.append("")
            lines.append(f"Total active: {len(active)}")

        elif report_type == "overdue":
            lines = ["OVERDUE BOOKS", "=" * 50, ""]
            overdue = [r for r in self.data["records"] if r["status"] == "Overdue"]
            if not overdue:
                lines.append("No overdue books. Great!")
            else:
                for r in overdue:
                    lines.append(f"{r['record_id']}  |  {r['book_id']} - {titles.get(r['book_id'], '?')}")
                    lines.append(f"   Borrower : {r['borrower_name']}")
                    lines.append(f"   Due Date : {r['due_date']}")
                    lines.append("")
            lines.append(f"Total overdue: {len(overdue)}")

        else:  # available summary
            lines = ["AVAILABLE BOOKS SUMMARY", "=" * 50, ""]
            for b in sorted(self.data["books"], key=lambda x: x["title"]):
                status = "AVAILABLE" if b["available_copies"] > 0 else "OUT OF STOCK"
                lines.append(f"{b['book_id']}  {b['title'][:35]:<35}  {b['available_copies']}/{b['total_copies']}  [{status}]")
            lines.append("")
            total_avail = sum(b["available_copies"] for b in self.data["books"])
            total_all = sum(b["total_copies"] for b in self.data["books"])
            lines.append(f"Total available copies: {total_avail} / {total_all}")

        self.report_text.insert(tk.END, "\n".join(lines))
        self.report_text.configure(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
