from scrapers.thehackernews import main as thehackernews_main
from scrapers.thecyberwire import main as thecyberwire_main
from scrapers.securityweek import main as securityweek_main
from scrapers.nask import main as nask_main
from scrapers.sekurak import main as sekurak_main
from scrapers.enisaeuropa import main as enisaeuropa_main
from scrapers.cybersecuritydive import main as cybersecuritydive_main
from clean_lastsaved_links import clean_lastsaved_links
from dotenv import load_dotenv
import time

# load HEADLESS (and other keys) from scrapers/.env — the scraper modules read
# os.getenv("HEADLESS") at launch time, and this runner is invoked directly
# (it doesn't import pinecone_sync, which is what loads dotenv on the main.py path)
load_dotenv(dotenv_path=".env")

# DYP-62: wipe every scraper's lastsaved_articlelink.txt before testing. The
# collectors stop at the first link equal to that pointer, so after a normal run
# a healthy scraper finds nothing new and still reports OK — testing nothing. An
# empty pointer matches no link, so each scraper re-fetches its listing in full.
# The collectors write the newest link back at the end of their run anyway.
clean_lastsaved_links()


# just trying to run the scrapers to check which one is alive and which one is not

# filled in by the try/except blocks below: stays "OK" unless the scraper raised
results = {
    "cybersecuritydive": "OK",
    "enisaeuropa": "OK",
    "nask": "OK",
    "securityweek": "OK",
    "sekurak": "OK",
    "thecyberwire": "OK",
    "thehackernews": "OK",
}


#CYBERSECURITYDIVE  failed
try:
    print("Running cybersecuritydive_main...")
    cybersecuritydive_main.main() 
except Exception as e:
    results["cybersecuritydive"] = f"FAILED: {e}"
    print(f"Error running cybersecuritydive_main: {e}")
finally:
    print("Finished running cybersecuritydive_main. Moving to the next scraper.")
    time.sleep(10)


#ENISAEUROPA    good
try:
    print("Running enisaeuropa_main...")
    enisaeuropa_main.main() 
except Exception as e:
    results["enisaeuropa"] = f"FAILED: {e}"
    print(f"Error running enisaeuropa_main: {e}")
finally:
    print("Finished running enisaeuropa_main. Moving to the next scraper.")
    time.sleep(10)


#NASK   good
try:
    print("Running nask_main...")
    nask_main.main() 
except Exception as e:
    results["nask"] = f"FAILED: {e}"
    print(f"Error running nask_main: {e}")
finally:
    print("Finished running nask_main. Moving to the next scraper.")
    time.sleep(10)


#SECURITYWEEK   good
try:
    print("Running securityweek_main...")
    securityweek_main.main()
except Exception as e:
    results["securityweek"] = f"FAILED: {e}"
    print(f"Error running securityweek_main: {e}")
finally:
    print("Finished running securityweek_main. Moving to the next scraper.")
    time.sleep(10)


#SEKURAK
try:
    print("Running sekurak_main...")
    sekurak_main.main()
except Exception as e:
    results["sekurak"] = f"FAILED: {e}"
    print(f"Error running sekurak_main: {e}")
finally:
    print("Finished running sekurak_main. Moving to the next scraper.")
    time.sleep(10)


#THECYBERWIRE   
try:
    print("Running thecyberwire_main...")
    thecyberwire_main.main()
except Exception as e:
    results["thecyberwire"] = f"FAILED: {e}"
    print(f"Error running thecyberwire_main: {e}")
finally:
    print("Finished running thecyberwire_main. Moving to the next scraper.")
    time.sleep(10)


#THEHACKERNEWS
try:
    print("Running thehackernews_main...")
    thehackernews_main.main()
except Exception as e:
    results["thehackernews"] = f"FAILED: {e}"
    print(f"Error running thehackernews_main: {e}")
finally:
    print("Finished running thehackernews_main. All scrapers have been tested.")
    time.sleep(10)


# ------------------------------- summary --------------------------------
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"{'Scraper':20} Result")
print("-" * 60)
for name, result in results.items():
    print(f"{name:20} {result}")
print("-" * 60)

good = [n for n, r in results.items() if r == "OK"]
bad = [n for n, r in results.items() if r != "OK"]
print(f"\n[+] Ran without errors: {', '.join(good) or 'none'}")
print(f"[-] Failed with errors: {', '.join(bad) or 'none'}")