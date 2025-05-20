from dotenv import load_dotenv
import os

from utils.bot_application import app

load_dotenv()

ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))

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
            print(msg)
            return

        return await handler_func(update, context)
    return wrapper


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

