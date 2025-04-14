import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# טוען את משתני הסביבה מקובץ .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# בדיקה בסיסית
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

# פקודת start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I'm alive via Local Bot API!")

# פקודת ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

# פונקציית ההפעלה
def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    print("✅ Bot is running with Local Bot API...")
    app.run_polling()

if __name__ == "__main__":
    main()