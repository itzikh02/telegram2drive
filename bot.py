import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes
import logging

# Load .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

logging.basicConfig(level=logging.WARNING)

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
        
        user_id = str(user.id)

        if user_id not in ALLOWED_USERS:
            msg = f"❌ Unauthorized access attempt by {user.full_name} (ID: {user_id})"
            logging.warning(msg)
            # await update.message.reply_text("🚫 Access denied.")
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

@authorized_only
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # ודא שיצרנו את התיקייה
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # קבל את הקובץ מכל סוג שהוא
    file = message.effective_attachment
    if not file:
        await message.reply_text("❌ לא הצלחתי לזהות קובץ.")
        return

    telegram_file = await file.get_file()
    original_filename = getattr(file, "file_name", f"{file.file_id}.bin")
    file_path = os.path.join(DOWNLOAD_DIR, original_filename)

    await message.reply_text(f"⬇️ מוריד את הקובץ: {original_filename}")
    await telegram_file.download_to_drive(file_path)
    await message.reply_text(f"✅ הקובץ נשמר בהצלחה: {original_filename}")

    # שלח ללוג
    await log_to_channel(
        context.application,
        f"📥 {message.from_user.full_name} שלח קובץ ונשמר בשם: {original_filename}"
    )

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .base_file_url("http://localhost:8081/file/bot") \
        .get_updates_base_url("http://localhost:8081") \
        .local_mode(True) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(None, handle_file))

    print("✅ Bot is running with Local Bot API and logging to Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()