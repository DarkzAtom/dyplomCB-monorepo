"""Build two baseline candidate sets scored against the same golden references:
lead-3 (first 3 sentences of the top retrieved article) and no-retrieval (GPT
answer with no context). Reads golden_workset.csv, writes golden_lead3.csv and
golden_noretrieval.csv - score each with rouge_eval.py. Run from app/.
"""

import csv
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

import openai  # noqa: E402

csv.field_size_limit(10_000_000)


def lead_3(text):
    sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(sentences[:3])


def top_article_text(retrieved):
    
    first_block = retrieved.split("\n\n[Article ")[0]
    lines = first_block.split("\n")
    # line 0 = '[Article 1] Title', line 1 = link, remainder = content
    return "\n".join(lines[2:]) if len(lines) > 2 else first_block


def no_retrieval_answer(client, question, model="gpt-4.1-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a cybersecurity news assistant. Answer the user's question."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def write_pairs(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["query", "reference", "candidate"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = list(csv.DictReader(open("golden_workset.csv", encoding="utf-8")))
    if not rows:
        sys.exit("golden_workset.csv is empty — run build_golden_set.py first")

    client = openai.OpenAI(api_key=os.getenv("OPENAI_APIKEY"))

    lead3_rows, noretr_rows = [], []
    for i, row in enumerate(rows, start=1):
        query = row["query"]
        reference = row["reference"]
        print(f"[{i}/{len(rows)}] {query}")

        lead3_rows.append({
            "query": query,
            "reference": reference,
            "candidate": lead_3(top_article_text(row["retrieved"])),
        })

        try:
            answer = no_retrieval_answer(client, query)
        except Exception as e:  # noqa: BLE001
            print(f"    no-retrieval failed: {e}")
            answer = ""
        noretr_rows.append({"query": query, "reference": reference, "candidate": answer})

    write_pairs("golden_lead3.csv", lead3_rows)
    write_pairs("golden_noretrieval.csv", noretr_rows)
    print("\nwrote golden_lead3.csv and golden_noretrieval.csv")
    print("score: python rouge_eval.py --csv golden_lead3.csv")
    print("       python rouge_eval.py --csv golden_noretrieval.csv")


if __name__ == "__main__":
    main()
