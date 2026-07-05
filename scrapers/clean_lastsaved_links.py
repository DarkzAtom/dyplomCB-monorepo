"""Reset every scraper's incremental pointer.

Each scraper keeps a `lastsaved_articlelink.txt` holding the newest article link
it has already collected. On the next run its all_links_collector stops as soon
as it hits that link (`if link == lastsaved_articlelink: break`), so only *newer*
articles are scraped.

This utility empties every one of those files, which makes each scraper treat
the whole listing as new again on the next run (nothing matches an empty string,
so nothing triggers the early break). Handy after a diagnostic run that advanced
the pointers, or to force a full re-scrape.

Run from the scrapers/ directory:  python clean_lastsaved_links.py
"""

from pathlib import Path

# scrapers/scrapers/<source>/lastsaved_articlelink.txt — found relative to THIS
# file, so the script works regardless of the current working directory.
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
