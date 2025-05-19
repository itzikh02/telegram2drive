from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters
from utils.bot_application import app

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text
    await send_message(update.effective_chat.id, f"Received: {user_response}")