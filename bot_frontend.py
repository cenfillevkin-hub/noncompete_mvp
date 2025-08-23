# bot_frontend.py
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# === CONFIGURATION ===
TELEGRAM_TOKEN = "7330586717:AAFIYkpo1yQ_vDLpZ0O_nztOy4YV_2HrWPg"  # replace with your actual bot token
BACKEND_URL = "http://127.0.0.1:8000/assess"     # your FastAPI assessment endpoint

# === HELPER FUNCTIONS ===
def extract_key_factor(user_text: str) -> str:
    """
    Very simple heuristic to find the main factor.
    For example, detect 'independent contractor', 'employee', 'trade secret', 'hardship'.
    """
    user_text_lower = user_text.lower()
    if "independent contractor" in user_text_lower:
        return "Independent Contractor vs Employee"
    if "trade secret" in user_text_lower:
        return "Trade Secret Exposure"
    if "hardship" in user_text_lower:
        return "Undue Hardship"
    return "General Contract Restriction"

# === TELEGRAM HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I can help you analyze non-compete or restrictive covenant situations.\n"
        "Please describe your contract restrictions in your own words. Try your best!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("Analyzing your case...")

    key_factor = extract_key_factor(user_text)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BACKEND_URL, json={"facts": user_text})
            response.raise_for_status()
            data = response.json()

            criteria = data.get("user_criteria", {})
            matched_cases = data.get("matched_cases", [])

            # Construct narrative
            msg = f"🔹 Key factor identified: {key_factor}\n\n"
            if criteria:
                msg += "✅ Relevant factors based on your input:\n"
                for k, v in criteria.items():
                    msg += f"- {k}: {v}\n"

            if matched_cases:
                msg += "\n🔎 Similar cases in the dataset:\n"
                for case_obj in matched_cases:
                    case = case_obj["case"]
                    jurisdiction = case.get("Jurisdiction/ Governing law", "Unknown")
                    summary = case.get("Narrative Summary", "No summary provided")
                    msg += f"\nIn [{jurisdiction}], a similar situation occurred:\n"
                    msg += f"\"{summary[:300]}...\"\n"
            else:
                msg += "\nNo closely matching cases were found, but this does not mean your situation is risk-free."

            msg += "\n\n⚖️ Note: These cases are for reference only. Legal outcomes depend on jurisdiction and full contract context."

            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"Error contacting backend: {e}")

# === MAIN FUNCTION ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
