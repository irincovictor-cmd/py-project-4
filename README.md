# School Library and Textbook Management System

A simple offline desktop prototype for managing school library books and classroom textbooks.

Built with Python and Tkinter. Data is stored locally in JSON. No internet or database server required.

## Features

- Book inventory (add, edit, delete, search)
- Pre-loaded starter books with cover images
- Borrow books (borrower name + due date)
- Return books
- Automatic overdue detection
- Simple reports (Borrowed, Overdue, Available summary)
- Data validation and confirmation dialogs
- Cover image support (PNG/JPG)

## Requirements

- Python 3.10 or newer
- Tkinter (included with most Python installations on Windows)
- Pillow (`pip install Pillow`) for image handling

## How to Run

```powershell
git clone https://github.com/irincovictor-cmd/py-project-4.git
cd py-project-4
python -m pip install -r requirements.txt
python main.py
```

On first launch the system creates `library_data.json` with 8 starter books and generates simple cover images in the `images/` folder (requires Pillow).

## Project Structure

- `main.py` – GUI and application logic
- `storage.py` – JSON load/save and helper functions
- `books_data.py` – Starter book definitions
- `images/` – Book cover images (auto-generated on first run)
- `tests/` – Automated tests
- `library_data.json` – Created at runtime (not committed)

## Notes

This is a classroom prototype for a single computer. It is not a multi-user networked library system.
