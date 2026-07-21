# -*- coding: utf-8 -*-
"""Test script for models.py — validates CRUD operations."""
from app.models import init_db, create_book, get_all_books, get_book_by_id, update_book, delete_book

# 1. Initialize the database
init_db()

# 2. Create a book
bid = create_book({
    "title": "La Odisea",
    "author": "Homero",
    "publisher": "Alianza Editorial",
    "translator": "Jose Luis Calvo",
    "reading_status": "No leído",
    "format": "digital"
})
print(f"[OK] Created book ID: {bid}")

# 3. Retrieve the book
book = get_book_by_id(bid)
assert book is not None, "Book should exist"
assert book["title"] == "La Odisea"
print(f"[OK] Retrieved: {book['title']} by {book['author']}")

# 4. Update reading status
update_book(bid, {"reading_status": "Leyendo"})
book2 = get_book_by_id(bid)
assert book2["reading_status"] == "Leyendo"
print(f"[OK] Updated status: {book2['reading_status']}")

# 5. List all books with search
results = get_all_books(search="Odisea")
assert len(results) >= 1
print(f"[OK] Search found: {len(results)} book(s)")

# 6. Delete the book
deleted = delete_book(bid)
assert deleted is not None
assert deleted["title"] == "La Odisea"
remaining = get_all_books()
print(f"[OK] Deleted. Books remaining: {len(remaining)}")

print("\n=== All models.py tests PASSED ===")
