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

from flask import Flask, request, jsonify

from database.db import (
    save_history,
    get_history,
    clear_history
)

import fitz
import os
import re
import traceback
import logging
import asyncio


# =========================================
# LOGGING
# =========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================================
# LOAD ENV
# =========================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY missing")


# =========================================
# GROQ CLIENT
# =========================================

client = Groq(api_key=GROQ_API_KEY)


# =========================================
# TELEGRAM APP
# =========================================

telegram_app = Application.builder().token(
    BOT_TOKEN
).build()


# =========================================
# FLASK APP
# =========================================

flask_app = Flask(__name__)


# =========================================
# CLEAN TEXT
# =========================================

def clean_text(text):

    if not text:
        return "No response generated."

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"#{1,6}", "", text)
    text = re.sub(r"```", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =========================================
# AI RESPONSE
# =========================================

def generate_ai_response(prompt):

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role": "system",
                "content": """
You are an advanced AI Study Assistant.

Rules:
- Telegram friendly formatting
- No markdown stars
- Easy explanations
- Use bullets
- Use emojis naturally
- Beginner friendly
- Educational tone
"""
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.7,
        max_tokens=2500

    )

    text = response.choices[0].message.content

    return clean_text(text)


# =========================================
# SEND REPLY
# =========================================

async def send_reply(update, text):

    text = clean_text(text)

    MAX_LENGTH = 4000

    for i in range(0, len(text), MAX_LENGTH):

        chunk = text[i:i + MAX_LENGTH]

        await update.message.reply_text(chunk)


# =========================================
# TYPING
# =========================================

async def typing_effect(update, context):

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )


# =========================================
# START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🧠 AI Study Assistant Bot

📚 Available Commands:

/ask <question>
/summarize <notes>
/quiz <topic>
/flashcards <topic>
/roadmap <career>
/exam <subject>
/practice <topic>

/history
/clearhistory

📄 Upload PDF for AI Summary.
"""

    await send_reply(update, text)


# =========================================
# GENERIC AI HANDLER
# =========================================

async def ai_command(update, context, prompt_template, history_tag=None):

    try:

        text = " ".join(context.args)

        if not text:

            await send_reply(
                update,
                "❌ Please provide input."
            )

            return

        await typing_effect(update, context)

        prompt = prompt_template.format(text=text)

        reply = generate_ai_response(prompt)

        if history_tag:

            save_history(
                str(update.effective_user.id),
                history_tag,
                text
            )

        await send_reply(update, reply)

    except Exception as e:

        logger.error(str(e))
        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================================
# COMMANDS
# =========================================

async def ask(update, context):

    await ai_command(
        update,
        context,
        """
Answer this educational question:

{text}

Requirements:
- Easy explanation
- Examples
- Beginner friendly
""",
        "ASK"
    )


async def summarize(update, context):

    await ai_command(
        update,
        context,
        """
Summarize these notes:

{text}

Requirements:
- Short notes
- Bullet points
- Revision format
""",
        "SUMMARIZE"
    )


async def quiz(update, context):

    await ai_command(
        update,
        context,
        """
Generate 10 MCQs on:

{text}

Include:
- Options
- Correct answers
- Explanations
"""
    )


async def flashcards(update, context):

    await ai_command(
        update,
        context,
        """
Create flashcards for:

{text}

Format:
Q:
A:
"""
    )


async def roadmap(update, context):

    await ai_command(
        update,
        context,
        """
Create roadmap for:

{text}

Include:
- Skills
- Timeline
- Projects
"""
    )


async def exam(update, context):

    await ai_command(
        update,
        context,
        """
Create exam preparation notes for:

{text}

Include:
- Important questions
- Key concepts
- Revision notes
"""
    )


async def practice(update, context):

    await ai_command(
        update,
        context,
        """
Generate practice questions on:

{text}

Include:
- MCQs
- Answers
- Mixed difficulty
"""
    )


# =========================================
# HISTORY
# =========================================

async def history(update, context):

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


# =========================================
# CLEAR HISTORY
# =========================================

async def clearhistory(update, context):

    clear_history(
        str(update.effective_user.id)
    )

    await send_reply(
        update,
        "🗑️ History cleared."
    )


# =========================================
# PDF HANDLER
# =========================================

async def handle_pdf(update, context):

    try:

        await send_reply(
            update,
            "📄 Processing PDF..."
        )

        document = update.message.document

        file = await context.bot.get_file(
            document.file_id
        )

        pdf_path = f"{document.file_unique_id}.pdf"

        await file.download_to_drive(pdf_path)

        pdf = fitz.open(pdf_path)

        text = ""

        for page in pdf:
            text += page.get_text()

        pdf.close()

        os.remove(pdf_path)

        prompt = f"""
Summarize this PDF:

{text[:12000]}

Requirements:
- Important concepts
- Bullet points
- Revision notes
"""

        reply = generate_ai_response(prompt)

        await send_reply(update, reply)

    except Exception as e:

        logger.error(str(e))
        traceback.print_exc()

        await send_reply(
            update,
            "❌ PDF processing failed."
        )


# =========================================
# NORMAL CHAT
# =========================================

async def handle_message(update, context):

    try:

        text = update.message.text

        if not text:
            return

        await typing_effect(update, context)

        prompt = f"""
Answer this educational question:

{text}
"""

        reply = generate_ai_response(prompt)

        await send_reply(update, reply)

    except Exception as e:

        logger.error(str(e))
        traceback.print_exc()

        await send_reply(
            update,
            "❌ AI service error."
        )


# =========================================
# REGISTER HANDLERS
# =========================================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", start))
telegram_app.add_handler(CommandHandler("ask", ask))
telegram_app.add_handler(CommandHandler("summarize", summarize))
telegram_app.add_handler(CommandHandler("quiz", quiz))
telegram_app.add_handler(CommandHandler("flashcards", flashcards))
telegram_app.add_handler(CommandHandler("roadmap", roadmap))
telegram_app.add_handler(CommandHandler("exam", exam))
telegram_app.add_handler(CommandHandler("practice", practice))
telegram_app.add_handler(CommandHandler("history", history))
telegram_app.add_handler(CommandHandler("clearhistory", clearhistory))

telegram_app.add_handler(
    MessageHandler(
        filters.Document.PDF,
        handle_pdf
    )
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)


# =========================================
# HOME ROUTE
# =========================================

@flask_app.route("/")
def home():

    return jsonify({
        "status": "running",
        "bot": "AI Study Assistant"
    })


# =========================================
# WEBHOOK ROUTE
# =========================================

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():

    try:

        json_data = request.get_json(force=True)

        update = Update.de_json(
            json_data,
            telegram_app.bot
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(
            telegram_app.process_update(update)
        )

        loop.close()

        return "ok", 200

    except Exception as e:

        logger.error(str(e))
        traceback.print_exc()

        return "error", 500


# =========================================
# STARTUP
# =========================================

async def startup():

    await telegram_app.initialize()

    webhook_url = (
        f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    )

    await telegram_app.bot.set_webhook(
        webhook_url
    )

    logger.info(
        f"Webhook Set: {webhook_url}"
    )


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(startup())

    print("🤖 AI Study Assistant Running")

    port = int(
        os.environ.get("PORT", 10000)
    )

    flask_app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )