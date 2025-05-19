from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
import asyncio
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

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    future = pending_responses.pop(chat_id, None)
    if future and not future.done():
        future.set_result(text)
    else:
        await update.message.reply_text("❗ לא ציפיתי לתשובה כרגע.")

pending_responses = {}  # chat_id -> Future

async def ask_user_input(chat_id: int, message: str) -> str:
    from utils.bot_application import app  # אם לא מיובא כבר

    await app.bot.send_message(chat_id=chat_id, text=message)

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    pending_responses[chat_id] = future

    try:
        response = await asyncio.wait_for(future, timeout=60)
        return response
    except asyncio.TimeoutError:
        pending_responses.pop(chat_id, None)
        return "⏰ זמן ההמתנה עבר"

