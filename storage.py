"""
Storage module for School Library and Textbook Management System.
Handles loading/saving of library data (books and borrow records) using JSON.
Also manages the images folder.
"""

import json
import os
from datetime import datetime, date
from copy import deepcopy

DATA_FILE = "library_data.json"
IMAGES_DIR = "images"


def get_base_dir():
    """Return the directory where this script lives."""
    return os.path.dirname(os.path.abspath(__file__))


def get_data_path():
    return os.path.join(get_base_dir(), DATA_FILE)


def get_images_dir():
    path = os.path.join(get_base_dir(), IMAGES_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def ensure_starter_images():
    """Create simple placeholder cover images for starter books if they are missing."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return  # Pillow not installed – skip image generation

    colors = {
        "B001": (70, 130, 180),
        "B002": (34, 139, 34),
        "B003": (178, 34, 34),
        "B004": (139, 69, 19),
        "B005": (128, 0, 128),
        "B006": (0, 100, 0),
        "B007": (0, 128, 128),
        "B008": (210, 105, 30),
    }
    titles = {
        "B001": "Elementary Algebra",
        "B002": "General Science",
        "B003": "English Communication",
        "B004": "Philippine History",
        "B005": "Basic Filipino",
        "B006": "World Atlas",
        "B007": "Introduction to Biology",
        "B008": "Reading Adventures",
    }
    categories = {
        "B001": "Mathematics",
        "B002": "Science",
        "B003": "English",
        "B004": "History",
        "B005": "Filipino",
        "B006": "Reference",
        "B007": "Science",
        "B008": "Literature",
    }

    img_dir = get_images_dir()
    for code, color in colors.items():
        path = os.path.join(img_dir, f"{code}.png")
        if os.path.exists(path):
            continue
        img = Image.new("RGB", (200, 280), color)
        draw = ImageDraw.Draw(img)
        draw.rectangle([5, 5, 194, 274], outline="white", width=3)

        title = titles.get(code, code)
        words = title.split()
        lines, current = [], ""
        for w in words:
            if len(current + " " + w) < 18:
                current = (current + " " + w).strip()
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)

        y = 80
        for line in lines:
            bbox = draw.textbbox((0, 0), line)
            w = bbox[2] - bbox[0]
            draw.text(((200 - w) // 2, y), line, fill="white")
            y += 25

        draw.text((20, 220), categories.get(code, ""), fill="white")
        draw.text((20, 245), code, fill="white")
        img.save(path)


def default_data():n    """Return a fresh data structure with starter books."""
    from books_data import STARTER_BOOKS
    return {
        "books": deepcopy(STARTER_BOOKS),
        "records": [],
        "next_book_id": 9,      # next after B008
        "next_record_id": 1
    }


def load_data():
    """Load library data from JSON. Create with starter books if missing."""
    ensure_starter_images()
    path = get_data_path()
    if not os.path.exists(path):
        data = default_data()
        save_data(data)
        return data

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure required keys exist
        if "books" not in data:
            data["books"] = []
        if "records" not in data:
            data["records"] = []
        if "next_book_id" not in data:
            data["next_book_id"] = 1
        if "next_record_id" not in data:
            data["next_record_id"] = 1
        return data
    except (json.JSONDecodeError, OSError):
        # Corrupted file – recreate
        data = default_data()
        save_data(data)
        return data


def save_data(data):
    """Save the entire data dictionary to JSON."""
    path = get_data_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_book_id(data):
    """Generate next book ID like B009."""
    book_id = f"B{data['next_book_id']:03d}"
    data["next_book_id"] += 1
    return book_id


def generate_record_id(data):
    """Generate next record ID like R001."""
    record_id = f"R{data['next_record_id']:03d}"
    data["next_record_id"] += 1
    return record_id


def today_str():
    """Return today's date as YYYY-MM-DD string."""
    return date.today().isoformat()


def parse_date(date_str):
    """Parse YYYY-MM-DD string to date object. Returns None on failure."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def is_overdue(record):
    """Return True if the record is still borrowed and past due date."""
    if record.get("status") != "Borrowed":
        return False
    due = parse_date(record.get("due_date"))
    if due is None:
        return False
    return date.today() > due


def update_overdue_statuses(data):
    """Update status of borrowed records that are past due date."""
    changed = False
    for rec in data["records"]:
        if rec.get("status") == "Borrowed" and is_overdue(rec):
            rec["status"] = "Overdue"
            changed = True
    if changed:
        save_data(data)
    return changed
