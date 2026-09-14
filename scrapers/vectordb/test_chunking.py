import os
from dotenv import load_dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

load_dotenv(dotenv_path=".env")
openai_apikey = os.getenv("OPENAI_APIKEY")

embedder = OpenAIEmbeddings(
    model="text-embedding-3-small", 
    openai_api_key=openai_apikey
)

text_splitter = SemanticChunker(
    embedder, 
    breakpoint_threshold_type="gradient",
)

# --- PASTE YOUR MESSY NEWS ARTICLE HERE ---
sample_article = """
President Donald Trump said Friday he was ordering all federal agencies to phase out use of Anthropic technology after the company’s unusually public dispute with the Pentagon over artificial intelligence safety.

Trump’s comments came just over an hour before the Pentagon’s deadline for Anthropic to allow unrestricted military use of its AI technology or face consequences — and nearly 24 hours after CEO Dario Amodei said his company “cannot in good conscience accede” to the Defense Department’s demands.

Anthropic didn’t immediately reply to a request for comment to Trump’s remarks.

At issue in the defense contract was a clash over AI’s role in national security and concerns about how increasingly capable machines could be used in high-stakes situations involving lethal force, sensitive information or government surveillance.

Anthropic, maker of the chatbot Claude, could afford to lose the contract. But the ultimatum this week from Defense Secretary Pete Hegseth posed broader risks at the peak of the company’s meteoric rise from a little-known computer science research lab in San Francisco to one of the world’s most valuable startups.

Anthropic spurns Pentagon’s latest proposal over its safeguards
If Amodei did not budge, military officials said they would not just pull Anthropic’s contract but also “deem them a supply chain risk,” a designation typically stamped on foreign adversaries that could derail the company’s critical partnerships with other businesses.

And if Amodei were to cave, he could lose trust in the booming AI industry, particularly from top talent drawn to the company for its promises of responsibly building better-than-human AI that, without safeguards, could pose catastrophic dangers.

Anthropic said it sought narrow assurances from the Pentagon that Claude won’t be used for mass surveillance of Americans or in fully autonomous weapons. But after months of private talks exploded into public debate, it said in a Thursday statement that new contract language “framed as compromise was paired with legalese that would allow those safeguards to be disregarded at will.”

That was after Sean Parnell, the Pentagon’s top spokesman, posted on social media that the military “has no interest in using AI to conduct mass surveillance of Americans (which is illegal) nor do we want to use AI to develop autonomous weapons that operate without human involvement.” He emphasized that the Pentagon wants to “use Anthropic’s model for all lawful purposes,” but he and other officials haven’t detailed how they want to use the technology.

Dispute further polarizes the tech industry
Emil Michael, the defense undersecretary for research and engineering, later lashed out at Amodei, alleging on X that he “has a God-complex” and “wants nothing more than to try to personally control the US Military and is ok putting our nation’s safety at risk.”

That message hasn’t resonated in much of Silicon Valley, where a growing number of tech workers from Anthropic’s top rivals, OpenAI and Google, voiced support for Amodei’s stand late Thursday in an open letter.

OpenAI and Google, along with Elon Musk’s xAI, also have contracts to supply their AI models to the military.

Musk sided with Trump’s Republican administration on Friday, saying on his social media platform X that “Anthropic hates Western Civilization” after Michael drew attention to a previous version of Claude’s guiding principles that encouraged “consideration of non-Western perspectives.” All of the leading AI models, including Musk’s Grok and OpenAI’s ChatGPT, are programmed with a set of instructions that guide a chatbot’s values and behavior. Anthropic calls that guidance a constitution.

While some Trump-allied tech leaders have joined the fray — including Musk and Palmer Luckey, co-founder of defense contractor Anduril — the polarizing debate over “woke AI” has put others in a difficult position.

“The Pentagon is negotiating with Google and OpenAI to try to get them to agree to what Anthropic has refused,” the open letter from some OpenAI and Google employees says. “They’re trying to divide each company with fear that the other will give in.”

But in a surprise move from one of Amodei’s fiercest rivals, OpenAI CEO Sam Altman on Friday sided with Anthropic and questioned the Pentagon’s “threatening” move in a CNBC interview, suggesting that OpenAI and most of the AI field share the same red lines. Amodei once worked for OpenAI before he and other OpenAI leaders quit to form Anthropic in 2021.

“For all the differences I have with Anthropic, I mostly trust them as a company, and I think they really do care about safety,” Altman told CNBC. “I’ve been happy that they’ve been supporting our warfighters. I’m not sure where this is going to go.”

Also raising concerns about the Pentagon’s approach were Republican and Democratic lawmakers and a former leader of the Defense Department’s AI initiatives.

“Painting a bullseye on Anthropic garners spicy headlines, but everyone loses in the end,” wrote retired Air Force Gen. Jack Shanahan in a social media post.

Shanahan faced a different wave of tech worker opposition during the first Trump administration when he led Maven, a project to use AI technology to analyze drone footage and target weapons. So many Google employees protested its participation in Project Maven at the time that the tech giant declined to renew the contract and then pledged not to use AI in weaponry.

“Since I was square in the middle of Project Maven & Google, it’s reasonable to assume I would take the Pentagon’s side here,” Shanahan wrote Thursday on social media. “Yet I’m sympathetic to Anthropic’s position. More so than I was to Google’s in 2018.”

He said Claude is already being widely used across the government, including in classified settings, and Anthropic’s red lines are “reasonable.” He said the AI large language models that power chatbots like Claude are also “not ready for prime time in national security settings,” particularly not for fully autonomous weapons.

“They’re not trying to play cute here,” he wrote.

Pentagon ready to punish Anthropic if it doesn’t compromise
Parnell asserted Thursday that opening up use of the technology would prevent the company from “jeopardizing critical military operations.”

“We will not let ANY company dictate the terms regarding how we make operational decisions,” Parnell wrote. Anthropic has “until 5:01 p.m. ET on Friday to decide” if it would meet the demands or face consequences.

When Hegseth and Amodei met on Tuesday, military officials warned that they could designate Anthropic as a supply chain risk, cancel its contract or invoke a Cold War-era law called the Defense Production Act to give the military more sweeping authority to use its products, even if the company doesn’t approve.

Amodei said Thursday that “those latter two threats are inherently contradictory: one labels us a security risk; the other labels Claude as essential to national security.” He said he hopes the Pentagon will reconsider given Claude’s value to the military, but, if not, Anthropic “will work to enable a smooth transition to another provider.”


"""

print("--- RUNNING LANGCHAIN SEMANTIC CHUNKER ---\n")

chunks = text_splitter.split_text(sample_article)

for i, chunk in enumerate(chunks):
    print(f"CHUNK {i + 1} (Words: {len(chunk.split())}):")
    print(chunk)
    print("-" * 60)
    
print(f"\nTotal chunks created: {len(chunks)}")