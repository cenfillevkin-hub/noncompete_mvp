import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Backend URL from environment (Render backend service URL)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Here are some top cases today:")
    try:
        response = requests.get(f"https://noncompete-backend.onrender.com/top_cases?n=3")
        top_cases = response.json().get("top_cases", [])
        for i, case in enumerate(top_cases, start=1):
            summary = case.get("Narrative Summary", "No summary available")
            await update.message.reply_text(f"Case {i}: {summary[:300]}...")
        await update.message.reply_text("Now, please describe your facts in a similar style.")
    except Exception as e:
        await update.message.reply_text(f"Error fetching top cases: {e}")

async def handle_facts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("Assessing your facts...")
    try:
        payload = {"facts": user_text}
        response = requests.post(f"https://noncompete-backend.onrender.com/assess", json=payload)
        result = response.json()
        criteria_text = "\n".join([f"{k}: {v}" for k, v in result.get("user_criteria", {}).items()])
        await update.message.reply_text(f"Extracted criteria:\n{criteria_text}")

        matches = result.get("matched_cases", [])
        if not matches:
            await update.message.reply_text("No closely matching cases found.")
        else:
            await update.message.reply_text("Similar cases:")
            for i, match in enumerate(matches, start=1):
                case = match["case"]
                summary = case.get("Narrative Summary", "No summary")
                score = match.get("match_score", 0)
                await update.message.reply_text(f"Case {i} (Score {score}): {summary[:300]}...")
    except Exception as e:
        await update.message.reply_text(f"Error assessing your facts: {e}")

if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_facts))
    print("Bot is running...")
    app.run_polling()
