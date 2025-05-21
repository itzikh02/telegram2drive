import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

import logging
from utils.bot_application import app
from utils.bot_utils import send_message, log_to_channel
from utils.auth_handler import auth_conv_handler
from utils.auth_utils import authorized_only
from utils.file_handler import handle_file, unsupported_file, file_handler

from utils.load_env import (
    BOT_TOKEN,
    ALLOWED_USERS,
    LOG_CHANNEL_ID,
    DRIVE_FOLDER_ID,
    DOWNLOAD_DIR,
    validate_env
)

validate_env()

# Set up logging to console
logging.basicConfig(level=logging.WARNING)

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