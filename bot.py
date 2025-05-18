import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from bot_utils import send_message
from drive_uploader import upload_file_to_drive
import logging, time, asyncio

# Load .env
load_dotenv()

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# Directory to save downloaded files on the bot server
DOWNLOAD_DIR = "downloads"

# Create the download directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Check if BOT_TOKEN is set
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")

# Set up logging to console
logging.basicConfig(level=logging.WARNING)

async def log_to_channel(application, message: str):
    """
    Send a log message to the specified Telegram channel.

    :param application: The Telegram application instance.
    :param message: The log message to send.
    """
    if LOG_CHANNEL_ID:
        try:
            await application.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📋 {message}")
        except Exception as e:
            logging.warning(f"Failed to send log to channel: {e}")

def authorized_only(handler_func):
    """
    Decorator to check if the user is authorized.
    If not, log the attempt and deny access.
    Use as a decorator (@) for command handlers.
    """
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
    """
    Retrieve a file from Telegram with retry logic.
    :param bot: The Telegram bot instance.
    :param file_id: The file ID to retrieve.
    :param retries: Number of retries before giving up.
    :param delay: Delay between retries in seconds.
    :return: The file object.
    """
    for attempt in range(retries):
        try:
            return await bot.get_file(file_id)
        except Exception as e:
            print(f"[DEBUG] Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(delay)
    raise TimeoutError("File retrieval failed after retries")

def wait_for_file_ready(path, size, timeout=60, interval=1):
    """
    Wait for a file to be ready by checking its size.
    :param path: Path to the file.
    :param size: Expected size of the file.
    :param timeout: Maximum time to wait in seconds.
    :param interval: Time to wait between checks in seconds.
    :return: True if the file is ready, False if timed out.
    """
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
            # print(f"[DEBUG] File size: {current_size} / {size} bytes", end='\r')
        time.sleep(interval)

    return False

@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command.
    :param update: The update object containing the message.
    :param context: The context object containing the bot instance.
    """
    await update.message.reply_text("👋 Welcome! Authorized access confirmed.")

    msg = f"✅ /start used by {update.effective_user.full_name} (ID: {update.effective_user.id})"
    await log_to_channel(context.application, msg)

@authorized_only
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /ping command.
    :param update: The update object containing the message.
    :param context: The context object containing the bot instance.
    """

    # await update.message.reply_text("🏓 Pong!")
    await send_message(context.application.bot, update.effective_user.id, "🏓 Pong!")

    msg = f"📡 /ping by {update.effective_user.full_name} (ID: {update.effective_user.id})"
    await log_to_channel(context.application, msg)


@authorized_only
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming files.
    :param update: The update object containing the message.
    :param context: The context object containing the bot instance.
    """

    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name
    file_size = document.file_size

    msg = f"[DEBUG] Received file: {file_name} ({file_size} bytes)"
    await log_to_channel(context.application, msg)

    try:
        tg_file = await get_file_with_retry(context.bot, file_id)
        file_path = tg_file.file_path
        local_path = os.path.join(DOWNLOAD_DIR, file_name)

        if not wait_for_file_ready(file_path, file_size, timeout=900, interval=1):
            msg = f"[DEBUG] File not ready after timeout: {file_path}"
            await log_to_channel(context.application, msg)
            raise TimeoutError("File not ready after timeout")


        with open(file_path, 'rb') as src, open(local_path, 'wb') as dst:
            downloaded = 0
            while True:
                chunk = src.read(8192)
                if not chunk:
                    break
                dst.write(chunk)
                downloaded += len(chunk)

        msg = f"[DEBUG] File copied to: {local_path}"
        await log_to_channel(context.application, msg)

        # Remove the file from the bot media temp folder after copying
        os.remove(file_path)

        msg = f"📥 Downloaded file: {file_name} ({file_size} bytes)"
        await log_to_channel(context.application, msg)

        # Upload to Google Drive
        drive_file_id = upload_file_to_drive(local_path, file_name, folder_id=DRIVE_FOLDER_ID)
        await update.message.reply_text(f"✅ File uploaded to Google Drive. File ID: {drive_file_id}")

    except Exception as e:
        await update.message.reply_text("❌ Failed to save file.")
        await log_to_channel(context.application, f"❌ Error saving file: {e}")

@authorized_only
async def unsupported_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle unsupported file types.
    :param update: The update object containing the message.
    :param context: The context object containing the bot instance.
    """
    await update.message.reply_text(
        "⚠️ Please send the file as a *Document* (not as a photo, video, or audio). Use the 📎 icon → File.",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .base_url("http://localhost:8081/bot") \
        .base_file_url("http://localhost:8081/file/") \
        .local_mode(True) \
        .build()

    file_handler = MessageHandler(filters.Document.ALL, handle_file)
    unsupported_handler = MessageHandler(
    filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.ANIMATION,
    unsupported_file)

    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    app.add_handler(file_handler)
    app.add_handler(unsupported_handler)

    print("✅ Bot is running with Local Bot API. Send /ping to check.")

    app.run_polling()

if __name__ == "__main__":
    main()