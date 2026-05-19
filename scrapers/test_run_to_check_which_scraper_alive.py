from scrapers.thehackernews import main as thehackernews_main
from scrapers.thecyberwire import main as thecyberwire_main
from scrapers.darkreading import main as darkreading_main
from scrapers.securityweek import main as securityweek_main
from scrapers.nask import main as nask_main
from scrapers.sekurak import main as sekurak_main
from scrapers.enisaeuropa import main as enisaeuropa_main
from scrapers.cybersecuritydive import main as cybersecuritydive_main
import time


# just trying to run the scrapers to check which one is alive and which one is not


#CYBERSECURITYDIVE  failed
try:
    print("Running cybersecuritydive_main...")
    cybersecuritydive_main.main() 
except Exception as e:
    print(f"Error running cybersecuritydive_main: {e}")
finally:
    print("Finished running cybersecuritydive_main. Moving to the next scraper.")
    time.sleep(10)


#ENISAEUROPA    good
try:
    print("Running enisaeuropa_main...")
    enisaeuropa_main.main() 
except Exception as e:
    print(f"Error running enisaeuropa_main: {e}")
finally:
    print("Finished running enisaeuropa_main. Moving to the next scraper.")
    time.sleep(10)


#NASK   good
try:
    print("Running nask_main...")
    nask_main.main() 
except Exception as e:
    print(f"Error running nask_main: {e}")
finally:
    print("Finished running nask_main. Moving to the next scraper.")
    time.sleep(10)


#SECURITYWEEK   good
try:
    print("Running securityweek_main...")
    securityweek_main.main()
except Exception as e:
    print(f"Error running securityweek_main: {e}")
finally:
    print("Finished running securityweek_main. Moving to the next scraper.")
    time.sleep(10)


#SEKURAK
try:
    print("Running sekurak_main...")
    sekurak_main.main()
except Exception as e:
    print(f"Error running sekurak_main: {e}")
finally:
    print("Finished running sekurak_main. Moving to the next scraper.")
    time.sleep(10)


#THECYBERWIRE   
try:
    print("Running thecyberwire_main...")
    thecyberwire_main.main()
except Exception as e:
    print(f"Error running thecyberwire_main: {e}")
finally:
    print("Finished running thecyberwire_main. Moving to the next scraper.")
    time.sleep(10)


#THEHACKERNEWS
try:
    print("Running thehackernews_main...")
    thehackernews_main.main()
except Exception as e:
    print(f"Error running thehackernews_main: {e}")
finally:
    print("Finished running thehackernews_main. Moving to the next scraper.")
    time.sleep(10)


#DARKREADING
try:
    print("Running darkreading_main...")
    darkreading_main.main()
except Exception as e:
    print(f"Error running darkreading_main: {e}")
finally:
    print("Finished running darkreading_main. All scrapers have been tested.")
    time.sleep(10)