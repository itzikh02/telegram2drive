import os, logging
from dotenv import load_dotenv

from utils.bot_application import app

# Load .env
load_dotenv()

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

async def send_message(chat_id: str | int, text: str):
    """
    Sends a message to a specified chat.
    :param chat_id: The ID of the chat to send the message to.
    :param text: The message text to send.
    """

    try:
        await app.bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")


async def log_to_channel(message: str):
    """
    Send a log message to the specified Telegram channel.

    :param application: The Telegram application instance.
    :param message: The log message to send.
    """
    if LOG_CHANNEL_ID:
        try:
            await send_message(chat_id=LOG_CHANNEL_ID, text=f"📋 {message}")
        except Exception as e:
            logging.warning(f"Failed to send log to channel: {e}")

