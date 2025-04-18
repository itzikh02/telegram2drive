import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from drive_uploader import upload_file_to_drive
import logging, time, asyncio

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

async def get_file_with_retry(bot, file_id, retries=10, delay=10):
    for attempt in range(retries):
        try:
            return await bot.get_file(file_id)
        except Exception as e:
            print(f"[DEBUG] Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(delay)
    raise TimeoutError("File retrieval failed after retries")


def wait_for_file_ready(path, size, timeout=60, interval=1):
    """Wait until file exists and size stops changing (download complete)."""
    start_time = time.time()
    last_size = -1

    time.sleep(2)

    if not os.path.exists(path):
        print(f"[DEBUG] File not found yet: {path}")

    while time.time() - start_time < timeout:
        if os.path.exists(path):
            current_size = os.path.getsize(path)
            if current_size == last_size:
                return True
            last_size = current_size
            print(f"[DEBUG] File size: {current_size} / {size} bytes", end='\r')
        time.sleep(interval)

    return False  # Timeout

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
    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name
    file_size = document.file_size

    print(f"[DEBUG] Received file: {file_name} ({file_size} bytes)")

    try:
        print("getting file...")
        tg_file = await get_file_with_retry(context.bot, file_id)
        file_path = tg_file.file_path
        
        print(f"[DEBUG] tg_file.file_path: {tg_file.file_path}")

        local_path = os.path.join(DOWNLOAD_DIR, file_name)

        print(f"[DEBUG] Waiting for file to be ready: {file_path}")

        if not wait_for_file_ready(file_path, file_size, timeout=900, interval=1):
            raise TimeoutError("File not ready after timeout")


        with open(file_path, 'rb') as src, open(local_path, 'wb') as dst:
            downloaded = 0
            while True:
                chunk = src.read(8192)
                if not chunk:
                    break
                dst.write(chunk)
                downloaded += len(chunk)
                print(f"[DEBUG] Copied {downloaded} / {file_size} bytes", end='\r')

        print(f"[DEBUG] File copied to: {local_path}")

        os.remove(file_path)
        print(f"[DEBUG] Deleted original file from bot storage: {file_path}")

        # שליחת אישור למשתמש
        await update.message.reply_text(f"✅ File saved as {file_name} in the downloads folder!")
        await log_to_channel(context.application, f"📥 Downloaded file: {file_name} ({file_size} bytes)")

        drive_file_id = upload_file_to_drive(local_path, file_name, folder_id="1nBEoFMF7VDzewTBuq1Pta8h2AR0vjZN3")
        await update.message.reply_text(f"📤 העלאה ל-Drive הושלמה! קובץ ID: {drive_file_id}")

    except Exception as e:
        print(f"[ERROR] Failed to copy file: {e}")
        await update.message.reply_text("❌ Failed to save file.")
        await log_to_channel(context.application, f"❌ Error saving file: {e}")

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