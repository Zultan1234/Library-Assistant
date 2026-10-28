"""Put the sample catalog back to its original state for another demo."""

import shutil
from pathlib import Path


base = Path(__file__).resolve().parent / "data"
source = base / "books_original.json"
target = base / "books.json"

if __name__ == "__main__":
    shutil.copyfile(source, target)
    print("Sample book data reset. All books are available again.")
