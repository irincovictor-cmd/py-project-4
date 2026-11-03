"""
Basic tests for storage and business logic of the Library system.
Run with: python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import date, timedelta

# Make sure parent directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import storage
from books_data import STARTER_BOOKS


class TestStorage(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory so we never touch real data
        self.test_dir = tempfile.mkdtemp()
        self.original_get_base = storage.get_base_dir
        storage.get_base_dir = lambda: self.test_dir

    def tearDown(self):
        storage.get_base_dir = self.original_get_base
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_data_has_starter_books(self):
        data = storage.default_data()
        self.assertEqual(len(data["books"]), len(STARTER_BOOKS))
        self.assertEqual(data["next_book_id"], 9)
        self.assertEqual(data["records"], [])

    def test_save_and_load(self):
        data = storage.default_data()
        storage.save_data(data)
        loaded = storage.load_data()
        self.assertEqual(len(loaded["books"]), 8)
        self.assertEqual(loaded["books"][0]["book_id"], "B001")

    def test_generate_ids(self):
        data = storage.default_data()
        bid = storage.generate_book_id(data)
        self.assertEqual(bid, "B009")
        self.assertEqual(data["next_book_id"], 10)

        rid = storage.generate_record_id(data)
        self.assertEqual(rid, "R001")
        self.assertEqual(data["next_record_id"], 2)

    def test_is_overdue(self):
        past = (date.today() - timedelta(days=3)).isoformat()
        future = (date.today() + timedelta(days=5)).isoformat()

        rec_overdue = {"status": "Borrowed", "due_date": past}
        rec_ok = {"status": "Borrowed", "due_date": future}
        rec_returned = {"status": "Returned", "due_date": past}

        self.assertTrue(storage.is_overdue(rec_overdue))
        self.assertFalse(storage.is_overdue(rec_ok))
        self.assertFalse(storage.is_overdue(rec_returned))

    def test_borrow_reduces_available(self):
        data = storage.default_data()
        book = data["books"][0]
        original = book["available_copies"]

        # Simulate borrow
        book["available_copies"] -= 1
        rec = {
            "record_id": "R001",
            "book_id": book["book_id"],
            "borrower_name": "Test Student",
            "borrow_date": storage.today_str(),
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
            "return_date": None,
            "status": "Borrowed"
        }
        data["records"].append(rec)
        storage.save_data(data)

        loaded = storage.load_data()
        loaded_book = next(b for b in loaded["books"] if b["book_id"] == book["book_id"])
        self.assertEqual(loaded_book["available_copies"], original - 1)
        self.assertEqual(len(loaded["records"]), 1)


if __name__ == "__main__":
    unittest.main()
