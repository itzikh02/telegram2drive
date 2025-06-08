import os
import pickle
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from utils.bot_utils import send_message, log_to_channel

# Load .env
load_dotenv()

# Load environment variables
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))


SCOPES = ['https://www.googleapis.com/auth/drive.file']

TOKEN_PATH = 'token.pickle'

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
            await log_to_channel(msg)

            return

        return await handler_func(update, context)
    return wrapper

async def check_auth():
    """
    Check if the user is authorized.
    If not, start the authorization process.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token_file:
            creds = pickle.load(token_file)

        if creds and creds.valid:
            return True

        elif creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'wb') as token_file:
                pickle.dump(creds, token_file)
            return True
    return False

auth_flows = {}

async def start_auth_conversation(user_id, update: Update):
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token_file:
            creds = pickle.load(token_file)

        if creds and creds.valid:
            await send_message(user_id, "✅ You're already authenticated with Google Drive.")
            return True

        elif creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'wb') as token_file:
                    pickle.dump(creds, token_file)
                await send_message(user_id, "🔁 Your token was successfully refreshed.")
                return True
            except Exception as e:
                log_to_channel(f"❌ Error refreshing token for user {user_id}: {e}")
                # os.remove(TOKEN_PATH)
                await send_message(user_id, "⚠️ Your previous token was expired or revoked. Please authorize again.")                

    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    auth_flows[user_id] = flow

    keyboard = [
        [InlineKeyboardButton("🔗 Authentication link", url=auth_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"🔗 Please authorize access, then paste the code here:", reply_markup=reply_markup)


async def finish_auth_conversation(user_id, code):
    flow = auth_flows.get(user_id)
    if not flow:
        await send_message(user_id, "⚠️ No active authorization flow. Please try /auth again.")
        return False
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open(TOKEN_PATH, 'wb') as token_file:
            pickle.dump(creds, token_file)
        await send_message(user_id, "✅ Google Drive authentication successful.")
        auth_flows.pop(user_id, None)
        return True
    except Exception as e:
        await send_message(user_id, f"❌ Authentication failed: {e}")
        return False