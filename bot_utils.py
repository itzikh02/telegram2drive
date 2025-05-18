from telegram import Bot

async def send_message(bot: Bot, chat_id: str | int, text: str):
    """
    שליחת הודעה דרך הבוט (עובד עם Local Bot API).
    
    :param bot: מופע הבוט (application.bot).
    :param chat_id: מזהה הצ'אט או המשתמש.
    :param text: תוכן ההודעה לשליחה.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")