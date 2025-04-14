import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Load .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

logging.basicConfig(level=logging.INFO)

# Function to send logs to Telegram channel
async def log_to_channel(application, message: str):
    if LOG_CHANNEL_ID:
        try:
            await application.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📋 {message}")
        except Exception as e:
            logging.warning(f"Failed to send log to channel: {e}")

# Authorization check
def authorized_only(handler_func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat

        if chat.type == "channel":
            print(f"📢 Message from channel: {chat.title} (ID: {chat.id})")
            logging.info(f"Message from channel: {chat.title} (ID: {chat.id})")

        user_id = str(user.id)

        if user_id not in ALLOWED_USERS:
            msg = f"❌ Unauthorized access attempt by {user.full_name} (ID: {user_id})"
            logging.warning(msg)
            await update.message.reply_text("🚫 Access denied.")
            await log_to_channel(context.application, msg)
            return

        return await handler_func(update, context)
    return wrapper

@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Authorized access confirmed.")
    await log_to_channel(context.application, f"✅ /start used by {update.effective_user.full_name} (ID: {update.effective_user.id})")

@authorized_only
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")
    await log_to_channel(context.application, f"📡 /ping by {update.effective_user.full_name} (ID: {update.effective_user.id})")

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    print("✅ Bot is running with Local Bot API and logging to Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()