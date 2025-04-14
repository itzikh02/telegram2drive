import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        return
    await update.message.reply_text("🤖 I'm alive!")

# Handler for all messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Filter by allowed users
    if user and user.id not in ALLOWED_USERS:
        return

    # ⚠️ TEMP: Print chat ID and name to console/log
    logger.info(
        f"📡 Incoming message from chat '{chat.title or user.full_name}' "
        f"(type: {chat.type}) - Chat ID: {chat.id}"
    )

    # Example action: echo message
    if update.message:
        await update.message.reply_text("✅ Message received.")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("🚀 Bot is starting...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())