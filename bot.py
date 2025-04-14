import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

#  start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I'm alive via Local Bot API!")

#  ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .get_updates_base_url("http://localhost:8081") \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    print("✅ Bot is running with Local Bot API...")
    app.run_polling()

if __name__ == "__main__":
    main()