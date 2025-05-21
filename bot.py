import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

from utils.bot_application import app
from utils.bot_utils import send_message, log_to_channel
from utils.drive_uploader import upload_file_to_drive
from utils.auth_handler import auth_conv_handler
from utils.auth_utils import authorized_only

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

# Check if .env is set and loaded correctly
required_env_vars = {
    "BOT_TOKEN": BOT_TOKEN,
    "ALLOWED_USERS": ALLOWED_USERS,
    "LOG_CHANNEL_ID": LOG_CHANNEL_ID,
    "DRIVE_FOLDER_ID": DRIVE_FOLDER_ID,
}

for name, value in required_env_vars.items():
    if not value:
        raise ValueError(f"{name} is not set in the .env file")

# Set up logging to console
logging.basicConfig(level=logging.WARNING)

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
    await send_message(update.effective_user.id, "👋 Welcome!")

    msg = f"✅ /start used by {update.effective_user.full_name} (ID: {update.effective_user.id})"
    await log_to_channel(msg)

@authorized_only
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /ping command.
    :param update: The update object containing the message.
    :param context: The context object containing the bot instance.
    """

    await send_message(update.effective_user.id, "🏓 Pong!")

    msg = f"📡 /ping by {update.effective_user.full_name} (ID: {update.effective_user.id})"
    await log_to_channel(msg)

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

    await log_to_channel(f"[DEBUG] Received file: {file_name} ({file_size} bytes)")

    progress_message = await update.message.reply_text("⬇️ Starting Upload...")

    await update.message.reply_chat_action("upload_document")

    try:
        tg_file = await get_file_with_retry(context.bot, file_id)
        file_path = tg_file.file_path
        local_path = os.path.join(DOWNLOAD_DIR, file_name)

        if not wait_for_file_ready(file_path, file_size, timeout=900, interval=1):
            await log_to_channel(f"[DEBUG] File not ready after timeout: {file_path}")

        with open(file_path, 'rb') as src, open(local_path, 'wb') as dst:
            
            downloaded = 0
            
            last_progress = 0
            while True:
                chunk = src.read(8192)
                if not chunk:
                    break
                dst.write(chunk)
                downloaded += len(chunk)
                progress_percent = int((downloaded / file_size) * 100)

                if progress_percent >= last_progress + 5:
                    last_progress = progress_percent
                    try:
                        await progress_message.edit_text(
                            f"📥 Uploading file: {progress_percent}% ({downloaded / (1024 * 1024):.2f} MB / {file_size / (1024 * 1024):.2f} MB)"
                        )
                    except Exception as e:
                        logging.warning(f"Failed to update progress message: {e}")


        await log_to_channel(f"[DEBUG] File copied to: {local_path}")

        # Remove the file from the bot media temp folder after copying
        os.remove(file_path)

        await log_to_channel(f"📥 Downloaded file: {file_name} ({file_size} bytes)")

        # Upload to Google 
        upload_file_to_drive(local_path, file_name, folder_id=DRIVE_FOLDER_ID)
        await update.message.reply_text(f"✅ File uploaded to Google Drive")

    except Exception as e:
        await send_message(update.effective_user.id, f"❌ Error: {e}")
        await log_to_channel(f"❌ Error saving file: {e}")

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

file_handler = MessageHandler(filters.Document.ALL, handle_file)
unsupported_handler = MessageHandler(
    filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.ANIMATION,
    unsupported_file)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))

app.add_handler(file_handler)
app.add_handler(unsupported_handler)
app.add_handler(auth_conv_handler)

print("✅ Bot is running with Local Bot API. Send /ping to check.")

app.run_polling()