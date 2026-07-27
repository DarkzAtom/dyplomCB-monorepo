from scrapers.thehackernews import main as thehackernews_main
from scrapers.thecyberwire import main as thecyberwire_main
from scrapers.securityweek import main as securityweek_main
from scrapers.nask import main as nask_main
from scrapers.sekurak import main as sekurak_main
from scrapers.enisaeuropa import main as enisaeuropa_main
from scrapers.cybersecuritydive import main as cybersecuritydive_main
from vectordb.pinecone_sync import main as pineconesync_main
import asyncio
import traceback


def run_step(label, func, *args):
    """Run one scrape/sync step in isolation.

    A failure in one source (network error, anti-bot block, parser change, …)
    is logged and swallowed so the *remaining* sources still scrape and still
    sync. Without this, any single exception aborts the whole script: every
    later source is skipped, the entire Pinecone-sync phase is skipped, and the
    scheduler then waits a full interval (6h) before retrying even the healthy
    sources.
    """
    print(f"[main] starting: {label}", flush=True)
    try:
        func(*args)
        print(f"[main] OK: {label}", flush=True)
    except Exception:
        print(f"[main] FAILED: {label} — continuing with the next step", flush=True)
        traceback.print_exc()


# --- Phase 1: run each scraper to collect data into its own output.csv ---
run_step("scrape cybersecuritydive", cybersecuritydive_main.main)
run_step("scrape enisaeuropa", enisaeuropa_main.main)
run_step("scrape nask", nask_main.main)
run_step("scrape securityweek", securityweek_main.main)
run_step("scrape sekurak", sekurak_main.main)
run_step("scrape thecyberwire", thecyberwire_main.main)
run_step("scrape thehackernews", thehackernews_main.main)

# --- Phase 2: vectorize each source's output.csv and upsert to Pinecone ---
run_step("sync cybersecuritydive", pineconesync_main, "scrapers/cybersecuritydive/output.csv")
run_step("sync enisaeuropa", pineconesync_main, "scrapers/enisaeuropa/output.csv")
run_step("sync nask", pineconesync_main, "scrapers/nask/output.csv")
run_step("sync securityweek", pineconesync_main, "scrapers/securityweek/output.csv")
run_step("sync sekurak", pineconesync_main, "scrapers/sekurak/output.csv")
run_step("sync thecyberwire", pineconesync_main, "scrapers/thecyberwire/output.csv")
run_step("sync thehackernews", pineconesync_main, "scrapers/thehackernews/output.csv")
