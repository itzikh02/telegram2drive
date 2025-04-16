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

    if not message:
        print("No message found in update.")
        return

    file_obj = None
    file_name = "unnamed"

    if message.document:
        file_obj = message.document
        file_name = file_obj.file_name or "unnamed_document"
    elif message.photo:
        file_obj = message.photo[-1]  # הכי איכותי
        file_name = f"photo_{file_obj.file_unique_id}.jpg"
    elif message.video:
        file_obj = message.video
        file_name = file_obj.file_name or f"video_{file_obj.file_unique_id}.mp4"
    elif message.audio:
        file_obj = message.audio
        file_name = file_obj.file_name or f"audio_{file_obj.file_unique_id}.mp3"
    elif message.voice:
        file_obj = message.voice
        file_name = f"voice_{file_obj.file_unique_id}.ogg"
    elif message.animation:
        file_obj = message.animation
        file_name = file_obj.file_name or f"animation_{file_obj.file_unique_id}.mp4"
    else:
        await message.reply_text("❗ לא זיהיתי סוג קובץ נתמך.")
        print("Unsupported file type.")
        return

    # קובץ מזהה
    file_id = file_obj.file_id
    print(f"Received file with ID: {file_id}")
    print(f"File name: {file_name}")

    # תיקייה
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    try:
        telegram_file = await context.bot.get_file(file_id)

        file_path = telegram_file.file_path
        print(f"Raw file_path: {file_path}")

        # תיקון זמני אם הוא נתיב מלא:
        if file_path.startswith("/"):
            file_path = file_path.split("/opt/telegram-bot-api/data/")[-1]  # מחלץ את הנתיב היחסי
            print(f"Fixed relative path: {file_path}")
            
        print(f"Telegram file object received.")
        print(f"Telegram file path (API): {telegram_file.file_path}")

        await telegram_file.download_to_drive(file_path)
        print(f"File downloaded to: {file_path}")

        await message.reply_text(f"✅ הקובץ נשמר בהצלחה: {file_name}")
        await log_to_channel(context.application, f"📥 קובץ התקבל ונשמר: {file_name}")
    except Exception as e:
        print(f"Error downloading file: {e}")
        await message.reply_text("❌ שגיאה בהורדת הקובץ.")


def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .base_file_url("http://localhost:8081/file/") \
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