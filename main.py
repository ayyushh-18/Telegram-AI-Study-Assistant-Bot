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

from database.db import (
    save_history,
    get_history,
    clear_history
)

import fitz
import os
import re
import traceback


# ---------------- LOAD ENV ---------------- #

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:

    raise ValueError(
        "Missing BOT_TOKEN or GROQ_API_KEY in .env"
    )


# ---------------- GROQ CLIENT ---------------- #

client = Groq(
    api_key=GROQ_API_KEY
)


# ---------------- CLEAN TEXT ---------------- #

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


# ---------------- AI RESPONSE ---------------- #

def generate_ai_response(prompt):

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role": "system",

                "content": """
You are an advanced AI Study Assistant.

Rules:
- Use Telegram-friendly formatting
- No markdown symbols
- No unnecessary stars
- Use emojis naturally
- Use bullet points
- Keep answers educational
- Keep formatting clean
- Keep answers detailed but readable
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


# ---------------- SEND REPLY ---------------- #

async def send_reply(update, text):

    MAX_LENGTH = 4000

    text = clean_text(text)

    for i in range(0, len(text), MAX_LENGTH):

        chunk = text[i:i + MAX_LENGTH]

        await update.message.reply_text(chunk)


# ---------------- TYPING EFFECT ---------------- #

async def typing_effect(update, context):

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )


# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🤖 Welcome to AI Study Assistant Bot

Your smart AI-powered learning companion.

📚 Features:
• AI Question Solving
• Smart Notes Summary
• MCQ Quiz Generator
• Flashcards
• Exam Preparation
• Learning Roadmaps
• PDF Notes Summary
• Practice Tests
• Chat History

👇 Use Menu Button to explore commands.
"""

    await send_reply(update, text)


# ---------------- ASK ---------------- #

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


# ---------------- SUMMARIZE ---------------- #

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):

    notes = " ".join(context.args)

    if not notes:

        await send_reply(
            update,
            "Usage:\n/summarize your notes"
        )

        return

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

    try:

        await send_reply(
            update,
            "📝 Summarizing..."
        )

        await typing_effect(update, context)

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


# ---------------- QUIZ ---------------- #

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    if not topic:

        await send_reply(
            update,
            "Usage:\n/quiz DBMS"
        )

        return

    prompt = f"""
Generate 10 MCQs on:

{topic}

Requirements:
- 4 options
- Correct answers
- Short explanation
- Beginner to advanced level
"""

    try:

        await send_reply(
            update,
            "🎯 Generating Quiz..."
        )

        await typing_effect(update, context)

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


# ---------------- FLASHCARDS ---------------- #

async def flashcards(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    if not topic:

        await send_reply(
            update,
            "Usage:\n/flashcards DBMS"
        )

        return

    prompt = f"""
Create flashcards for:

{topic}

Requirements:
- Question-answer format
- Important concepts only
- Easy revision notes
"""

    try:

        await send_reply(
            update,
            "🧠 Creating Flashcards..."
        )

        await typing_effect(update, context)

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


# ---------------- ROADMAP ---------------- #

async def roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):

    career = " ".join(context.args)

    if not career:

        await send_reply(
            update,
            "Usage:\n/roadmap Python Developer"
        )

        return

    prompt = f"""
Create a complete roadmap for:

{career}

Include:
- Skills
- Learning order
- Projects
- Resources
- Timeline
- Career advice
"""

    try:

        await send_reply(
            update,
            "🛣️ Generating Roadmap..."
        )

        await typing_effect(update, context)

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


# ---------------- HISTORY ---------------- #

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


# ---------------- CLEAR HISTORY ---------------- #

async def clearhistory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    clear_history(
        str(update.effective_user.id)
    )

    await send_reply(
        update,
        "🗑️ History cleared successfully."
    )


# ---------------- EXAM MODE ---------------- #

async def exam(update: Update, context: ContextTypes.DEFAULT_TYPE):

    subject = " ".join(context.args)

    if not subject:

        await send_reply(
            update,
            "Usage:\n/exam DBMS"
        )

        return

    prompt = f"""
Create exam preparation notes for:

{subject}

Include:
- Important questions
- Viva questions
- Revision notes
- Important concepts
- Short tricks
"""

    try:

        await send_reply(
            update,
            "📚 Preparing Exam Kit..."
        )

        await typing_effect(update, context)

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


# ---------------- PRACTICE ---------------- #

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    topic = " ".join(context.args)

    if not topic:

        await send_reply(
            update,
            "Usage:\n/practice Python"
        )

        return

    prompt = f"""
Generate a complete practice test on:

{topic}

Requirements:
- 20 MCQs
- 4 options
- Correct answer after each question
- Beginner to advanced level
"""

    try:

        await send_reply(
            update,
            "🧪 Generating Practice Test..."
        )

        await typing_effect(update, context)

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


# ---------------- PDF SUMMARIZER ---------------- #

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

        pdf_path = "uploaded_notes.pdf"

        await file.download_to_drive(pdf_path)

        text = ""

        pdf = fitz.open(pdf_path)

        for page in pdf:

            text += page.get_text()

        pdf.close()

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


# ---------------- MAIN APP ---------------- #

app = Application.builder().token(BOT_TOKEN).build()


# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", start))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(CommandHandler("summarize", summarize))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(CommandHandler("flashcards", flashcards))
app.add_handler(CommandHandler("roadmap", roadmap))
app.add_handler(CommandHandler("history", history))
app.add_handler(CommandHandler("clearhistory", clearhistory))
app.add_handler(CommandHandler("exam", exam))
app.add_handler(CommandHandler("practice", practice))


# PDF Upload
app.add_handler(
    MessageHandler(
        filters.Document.PDF,
        handle_pdf
    )
)


print("🤖 Bot Running...")


# Run Bot
app.run_polling()