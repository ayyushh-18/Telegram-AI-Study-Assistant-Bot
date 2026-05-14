from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from telegram.constants import ChatAction

from dotenv import load_dotenv
from groq import Groq

from flask import Flask, request

from database.db import (
    save_history,
    get_history,
    clear_history
)

import fitz
import os
import re
import traceback
import asyncio
import logging


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================
# LOAD ENV
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError(
        "Missing BOT_TOKEN or GROQ_API_KEY"
    )


# =========================
# GROQ CLIENT
# =========================

client = Groq(
    api_key=GROQ_API_KEY
)


# =========================
# TELEGRAM APP
# =========================

telegram_app = Application.builder().token(
    BOT_TOKEN
).build()


# =========================
# FLASK APP
# =========================

flask_app = Flask(__name__)


# =========================
# CLEAN TEXT
# =========================

def clean_text(text):

    if not text:
        return "No response generated."

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"#{1,6}", "", text)
    text = re.sub(r"```", "", text)
    text = re.sub(r"---+", "", text)
    text = re.sub(r"===+", "", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =========================
# AI RESPONSE
# =========================

def generate_ai_response(prompt):

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role": "system",

                "content": """
You are an advanced AI Study Assistant.

Rules:
- Telegram-friendly formatting
- No markdown stars
- No unnecessary symbols
- Use clean bullet points
- Use emojis naturally
- Educational tone
- Detailed but readable answers
"""
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.7,
        max_tokens=5000

    )

    text = response.choices[0].message.content

    return clean_text(text)


# =========================
# SEND REPLY
# =========================

async def send_reply(update, text):

    MAX_LENGTH = 4000

    text = clean_text(text)

    for i in range(0, len(text), MAX_LENGTH):

        chunk = text[i:i + MAX_LENGTH]

        await update.message.reply_text(chunk)


# =========================
# TYPING EFFECT
# =========================

async def typing_effect(update, context):

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🤖 AI Study Assistant Bot

📚 Features:
• AI Question Solving
• Notes Summary
• MCQ Quiz Generator
• Flashcards
• Exam Preparation
• Roadmaps
• Practice Tests
• PDF Summary
• History Tracking

🧠 Commands:

/ask <question>
/summarize <notes>
/quiz <topic>
/flashcards <topic>
/roadmap <career>
/history
/clearhistory
/exam <subject>
/practice <topic>

📄 Upload PDF for AI Summary.
"""

    await send_reply(update, text)


# =========================
# ASK
# =========================

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):

    question = " ".join(context.args)

    if not question:

        await send_reply(
            update,
            "Usage:\n/ask What is DBMS?"
        )

        return

    try:

        await send_reply(
            update,
            "🤔 Thinking..."
        )

        await typing_effect(update, context)

        prompt = f"""
Answer this educational question:

{question}

Requirements:
- Easy explanation
- Examples
- Bullet points
- Beginner-friendly
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "ASK",
            question
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# SUMMARIZE
# =========================

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):

    notes = " ".join(context.args)

    if not notes:

        await send_reply(
            update,
            "Usage:\n/summarize your notes"
        )

        return

    try:

        await send_reply(
            update,
            "📝 Summarizing..."
        )

        await typing_effect(update, context)

        prompt = f"""
Summarize these notes.

Requirements:
- Short bullet points
- Important concepts
- Easy revision format
- Beginner-friendly

Notes:
{notes}
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "SUMMARIZE",
            notes
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# QUIZ
# =========================

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    if not topic:

        await send_reply(
            update,
            "Usage:\n/quiz DBMS"
        )

        return

    try:

        await send_reply(
            update,
            "🎯 Generating Quiz..."
        )

        await typing_effect(update, context)

        prompt = f"""
Generate 10 MCQs on:

{topic}

Requirements:
- 4 options
- Correct answers
- Short explanations
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "QUIZ",
            topic
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# FLASHCARDS
# =========================

async def flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    if not topic:

        await send_reply(
            update,
            "Usage:\n/flashcards DBMS"
        )

        return

    try:

        await send_reply(
            update,
            "🧠 Creating Flashcards..."
        )

        await typing_effect(update, context)

        prompt = f"""
Create flashcards for:

{topic}

Format:
Q:
A:
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "FLASHCARDS",
            topic
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# ROADMAP
# =========================

async def roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):

    career = " ".join(context.args)

    if not career:

        await send_reply(
            update,
            "Usage:\n/roadmap Python Developer"
        )

        return

    try:

        await send_reply(
            update,
            "🛣️ Generating Roadmap..."
        )

        await typing_effect(update, context)

        prompt = f"""
Create a roadmap for:

{career}

Include:
- Skills
- Learning order
- Projects
- Resources
- Timeline
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "ROADMAP",
            career
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# HISTORY
# =========================

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):

    records = get_history(
        str(update.effective_user.id)
    )

    if not records:

        await send_reply(
            update,
            "No history found."
        )

        return

    text = "📜 Recent History:\n\n"

    for command, content in records:

        text += f"🔹 [{command}] {content}\n\n"

    await send_reply(update, text)


# =========================
# CLEAR HISTORY
# =========================

async def clearhistory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    clear_history(
        str(update.effective_user.id)
    )

    await send_reply(
        update,
        "🗑️ History cleared."
    )


# =========================
# EXAM
# =========================

async def exam(update: Update, context: ContextTypes.DEFAULT_TYPE):

    subject = " ".join(context.args)

    if not subject:

        await send_reply(
            update,
            "Usage:\n/exam DBMS"
        )

        return

    try:

        await send_reply(
            update,
            "📚 Preparing Exam Notes..."
        )

        await typing_effect(update, context)

        prompt = f"""
Create exam preparation notes for:

{subject}

Include:
- Important questions
- Viva questions
- Revision notes
- Key concepts
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "EXAM",
            subject
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# PRACTICE
# =========================

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    if not topic:

        await send_reply(
            update,
            "Usage:\n/practice Python"
        )

        return

    try:

        await send_reply(
            update,
            "🧪 Generating Practice Test..."
        )

        await typing_effect(update, context)

        prompt = f"""
Generate a practice test on:

{topic}

Requirements:
- 20 MCQs
- Correct answers
- Mixed difficulty
"""

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "PRACTICE",
            topic
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================
# PDF HANDLER
# =========================

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        await send_reply(
            update,
            "📄 Processing PDF..."
        )

        document = update.message.document

        if document.mime_type != "application/pdf":

            await send_reply(
                update,
                "Please upload a valid PDF."
            )

            return

        file = await context.bot.get_file(
            document.file_id
        )

        pdf_path = f"{document.file_unique_id}.pdf"

        await file.download_to_drive(pdf_path)

        text = ""

        pdf = fitz.open(pdf_path)

        for page in pdf:
            text += page.get_text()

        pdf.close()

        os.remove(pdf_path)

        prompt = f"""
Summarize these PDF notes.

Requirements:
- Important concepts
- Bullet points
- Revision notes
- Easy language

PDF Content:
{text[:12000]}
"""

        await typing_effect(update, context)

        reply = generate_ai_response(prompt)

        save_history(
            str(update.effective_user.id),
            "PDF_SUMMARY",
            document.file_name
        )

        await send_reply(update, reply)

    except Exception:

        traceback.print_exc()

        await send_reply(
            update,
            "❌ PDF processing error."
        )


# =========================
# ADD HANDLERS
# =========================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", start))
telegram_app.add_handler(CommandHandler("ask", ask))
telegram_app.add_handler(CommandHandler("summarize", summarize))
telegram_app.add_handler(CommandHandler("quiz", quiz))
telegram_app.add_handler(CommandHandler("flashcards", flashcards))
telegram_app.add_handler(CommandHandler("roadmap", roadmap))
telegram_app.add_handler(CommandHandler("history", history))
telegram_app.add_handler(CommandHandler("clearhistory", clearhistory))
telegram_app.add_handler(CommandHandler("exam", exam))
telegram_app.add_handler(CommandHandler("practice", practice))

telegram_app.add_handler(
    MessageHandler(
        filters.Document.PDF,
        handle_pdf
    )
)


# =========================
# FLASK ROUTES
# =========================

@flask_app.route("/")
def home():
    return "AI Study Assistant Bot Running"


@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():

    try:

        data = request.get_json(force=True)

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        await telegram_app.process_update(update)

        return "ok"

    except Exception:

        traceback.print_exc()

        return "error"


# =========================
# STARTUP
# =========================

async def setup():

    await telegram_app.initialize()

    webhook_url = (
        f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    )

    await telegram_app.bot.set_webhook(
        webhook_url
    )

    print(f"Webhook Set: {webhook_url}")


if __name__ == "__main__":

    async def start_bot():

        await telegram_app.initialize()

        if RENDER_EXTERNAL_URL:

            webhook_url = (
                f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
            )

            await telegram_app.bot.set_webhook(
                webhook_url
            )

            print(f"Webhook Set: {webhook_url}")

    asyncio.run(start_bot())

    print("🤖 Bot Running...")

    port = int(
        os.environ.get("PORT", 10000)
    )

    flask_app.run(
        host="0.0.0.0",
        port=port
    )