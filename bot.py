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
    # בודק אם יש קובץ שנשלח (מסמך או תמונה)
    file = update.message.document or update.message.photo[-1] if update.message.photo else None

    if file:
        # קבלת אובייקט הקובץ המלא
        telegram_file = await file.get_file()
        # הדפסת ה־file_path
        print(f"File path: {telegram_file.file_path}")

        # שמירת הקובץ בתיקייה בפרויקט
        file_path = telegram_file.file_path
        download_url = f"http://localhost:8081/file/{BOT_TOKEN}/{file_path}"

        # הורדת הקובץ
        print(f"Download URL: {download_url}")

        # הגדרת שם הקובץ לשמירה בשרת
        file_name = file_path.split("/")[-1]
        local_path = os.path.join("downloads", file_name)

        # הורדת הקובץ לשרת
        try:
            await telegram_file.download_to_drive(local_path)
            print(f"File downloaded successfully to {local_path}")

            # שלח הודעה שההורדה הושלמה
            await update.message.reply_text(f"✅ Download completed! File saved to: {local_path}")

        except Exception as e:
            print(f"Failed to download file: {e}")
            await update.message.reply_text(f"❌ Failed to download file. Error: {e}")

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .base_file_url("http://localhost:8081/file/bot") \
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