"""Telegram bot front-end for the RAG chat (DYP-50 / DYP-54).

A thin second client over the existing pipeline: every text message is passed
to retriever.process_user_query (query refinement -> embedding -> Pinecone
search -> GPT answer with source links) and the answer is sent back to the
chat. The retriever is imported directly, so the FastAPI app does not need to
be running.

Setup:
    add TELEGRAM_BOT_TOKEN=<token from @BotFather> to app/.env
Run:
    cd app && python telegram_bot.py
"""

import asyncio
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import retriever

load_dotenv(dotenv_path=".env")

# Telegram rejects messages longer than 4096 chars — long answers are split
# on line boundaries and sent as several messages.
TELEGRAM_MESSAGE_LIMIT = 4096


def split_for_telegram(text, limit=TELEGRAM_MESSAGE_LIMIT):
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    chunks.append(text)
    return chunks


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I answer questions about recent cybersecurity news. "
        'Just ask, e.g. "any news about ransomware attacks?"'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.chat.send_action(ChatAction.TYPING)

    # process_user_query is synchronous (OpenAI + Pinecone calls) — run it in
    # a worker thread so the bot's event loop stays responsive
    try:
        answer = await asyncio.to_thread(retriever.process_user_query, query)
    except Exception as e:
        answer = f"Error: {e}"

    if not answer:
        answer = "Sorry, I couldn't produce an answer for that."

    for chunk in split_for_telegram(answer):
        await update.message.reply_text(chunk)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set — add it to app/.env")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("telegram bot is polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
