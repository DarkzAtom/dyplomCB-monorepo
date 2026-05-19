from scrapers.thehackernews import main as thehackernews_main
from scrapers.thecyberwire import main as thecyberwire_main
from scrapers.darkreading import main as darkreading_main
from scrapers.securityweek import main as securityweek_main
from scrapers.nask import main as nask_main
from scrapers.sekurak import main as sekurak_main
from scrapers.enisaeuropa import main as enisaeuropa_main
from scrapers.cybersecuritydive import main as cybersecuritydive_main
from vectordb.pinecone_sync import main as pineconesync_main
import asyncio

# running scrapers to collect data and save it to csv files in respective folders
cybersecuritydive_main.main()
enisaeuropa_main.main()
nask_main.main()
securityweek_main.main()
sekurak_main.main()
thecyberwire_main.main()
thehackernews_main.main()

# adding vectorization of every output 
pineconesync_main("scrapers/cybersecuritydive/output.csv")
pineconesync_main("scrapers/enisaeuropa/output.csv")
pineconesync_main("scrapers/nask/output.csv")
pineconesync_main("scrapers/securityweek/output.csv")
pineconesync_main("scrapers/sekurak/output.csv")
pineconesync_main("scrapers/thecyberwire/output.csv")
pineconesync_main("scrapers/thehackernews/output.csv")