import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)  # מופע עצמאי

async def send_message(chat_id: str | int, text: str):
    """
    שליחת הודעה דרך הבוט בצורה עצמאית.
    
    :param chat_id: מזהה הצ'אט או המשתמש.
    :param text: תוכן ההודעה לשליחה.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")