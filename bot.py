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

    # Detect file type and assign filename
    if message.document:
        file_obj = message.document
        file_name = file_obj.file_name or "unnamed_document"
    elif message.photo:
        file_obj = message.photo[-1]  # Highest quality photo
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
        await message.reply_text("❗ Unsupported file type.")
        print("Unsupported file type.")
        return

    file_id = file_obj.file_id
    print(f"Received file with ID: {file_id}")
    print(f"File name: {file_name}")

    # Create downloads directory if needed
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_save_path = os.path.join(DOWNLOAD_DIR, file_name)

    try:
        telegram_file = await context.bot.get_file(file_id)
        print("Telegram file object received.")
        print(f"Raw file_path: {telegram_file.file_path}")

        # Fix file path if it is a full URL instead of relative path
        if telegram_file.file_path.startswith("http://"):
            print("⚠️ Detected full URL in file_path. Extracting relative path...")
            parts = telegram_file.file_path.split("/file/")[-1].split("/", 1)
            if len(parts) == 2:
                file_path_relative = parts[1]
                print(f"✅ Cleaned relative path: {file_path_relative}")
            else:
                print("❗ Unable to extract relative path from URL.")
                return
        else:
            file_path_relative = telegram_file.file_path  # Already relative

        print(f"Raw file_path 2: {telegram_file.file_path}")

        # Download the file using download_to_drive() for local file storage
        await telegram_file.download_to_drive(local_save_path)
        print(f"File downloaded to: {local_save_path}")

        await message.reply_text(f"✅ The file has been successfully saved: {file_name}")
        await log_to_channel(context.application, f"📥 File received and saved: {file_name}")
    except Exception as e:
        print(f"Error downloading file: {e}")
        await message.reply_text("❌ Error downloading the file.")

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