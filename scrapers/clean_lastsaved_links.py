"""Empty every scraper's lastsaved_articlelink.txt so the next run re-scrapes the
whole listing (an empty pointer matches nothing, so the early-break never fires).
Handy after a diagnostic run advanced the pointers. Run from scrapers/.
"""

from pathlib import Path

# scrapers/scrapers/<source>/lastsaved_articlelink.txt — found relative to THIS file, so the script works regardless of the current working directory.
SCRAPERS_DIR = Path(__file__).resolve().parent / "scrapers"


def clean_lastsaved_links():
    files = sorted(SCRAPERS_DIR.glob("*/lastsaved_articlelink.txt"))
    if not files:
        print(f"No lastsaved_articlelink.txt files found under {SCRAPERS_DIR}")
        return

    for f in files:
        previous = f.read_text(encoding="utf-8").strip()
        f.write_text("", encoding="utf-8")
        source = f.parent.name
        print(f"cleaned {source:20} (was: {previous or '<empty>'})")

    print(f"\nDone — reset {len(files)} pointer file(s).")


if __name__ == "__main__":
    clean_lastsaved_links()
