from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

from utils.bot_utils import send_message
from utils.drive_auth import start_auth_conversation, finish_auth_conversation

AUTH_CODE = range(1)

async def auth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await start_auth_conversation(user_id)
    return AUTH_CODE

async def auth_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    code = update.message.text.strip()
    await finish_auth_conversation(user_id, code)
    return ConversationHandler.END

async def auth_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(update.effective_user.id, "❌ Authentication canceled.")
    return ConversationHandler.END

auth_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("auth", auth_start)],
    states={AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, auth_code_received)]},
    fallbacks=[CommandHandler("cancel", auth_cancel)]
)