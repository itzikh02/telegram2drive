import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
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
    file_name = None
    file_id = None

    # תופס כל סוג של קובץ שנשלח
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
    elif message.photo:
        file_id = message.photo[-1].file_id  # מקבל את התמונה הכי באיכות
        file_name = f"photo_{file_id}.jpg"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or f"video_{file_id}.mp4"
    else:
        await message.reply_text("❗ לא זוהה קובץ נתמך להורדה.")
        return

    # וידוא שהספרייה קיימת
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    try:
        telegram_file = await context.bot.get_file(file_id)
        await telegram_file.download_to_drive(file_path)

        await message.reply_text(f"✅ הקובץ '{file_name}' ירד בהצלחה.")
        print(f"Downloaded to: {file_path}")
    except Exception as e:
        await message.reply_text("❌ שגיאה בהורדת הקובץ.")
        print(f"Error downloading file: {e}")


def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .base_file_url("http://localhost:8081/file") \
        .local_mode(True) \
        .build()

    file_handler = MessageHandler(filters.ALL, handle_file)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(file_handler)

    print("✅ Bot is running with Local Bot API and logging to Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()