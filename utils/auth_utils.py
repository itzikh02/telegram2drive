import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from google.auth.transport.requests import Request

# Reconstruct credentials object from raw token data
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from utils.bot_utils import send_message, log_to_channel

import requests
import time
import json

# Load .env
load_dotenv()

# Load environment variables
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))


SCOPES = ['https://www.googleapis.com/auth/drive.file']

TOKEN_PATH = 'token.json'

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
    Check if the user is authorized using the token from device flow.
    """

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token_file:
            token_data = json.load(token_file)

        with open("credentials.json") as f:
            client_info = json.load(f)["installed"]

        client_id = client_info["client_id"]
        client_secret = client_info.get("client_secret")
        scope = "https://www.googleapis.com/auth/drive.file"

        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[scope]
        )

        if creds and creds.valid:
            return True

        # Refresh if needed
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save updated credentials
                updated_token_data = {
                    "access_token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "scope": scope,
                    "token_type": "Bearer",
                    "expiry": creds.expiry.isoformat() if creds.expiry else None,
                }
                with open(TOKEN_PATH, 'w') as token_file:
                    json.dump(updated_token_data, token_file)
            except Exception:
                return False
            
        return True
    return False

def require_auth(handler_func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await check_auth():
            await send_message(update.effective_user.id, "🔐 Please authenticate first with /auth")
            return
        return await handler_func(update, context)
    return wrapper

auth_flows = {}

@authorized_only
async def auth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start the OAuth device flow using 'TV and Limited Input' client.
    """
    user_id = str(update.effective_user.id)
    if await check_auth():
        await send_message(user_id, "🔐 You are already authenticated.")
        return True

    with open("credentials.json") as f:
        client_info = json.load(f)["installed"]

    client_id = client_info["client_id"]
    client_secret = client_info.get("client_secret")  # Optional for installed apps

    scope = "https://www.googleapis.com/auth/drive.file"

    # Step 1: Request device and user code
    device_code_response = requests.post(
        "https://oauth2.googleapis.com/device/code",
        data={
            "client_id": client_id,
            "scope": scope
        },
    ).json()

    user_code = device_code_response["user_code"]
    verification_url = device_code_response["verification_url"]
    device_code = device_code_response["device_code"]
    interval = device_code_response.get("interval", 5)

    # Step 2: Prompt user to visit the URL and enter the code
    await update.message.reply_text(
        f"🔐 To authorize the bot to access your Google Drive:\n\n"
        f"1. Go to: {verification_url}\n"
        f"2. Enter the code: `{user_code}`\n\n"
        f"The bot will wait until you complete the authorization.",
        parse_mode="Markdown"
    )

    # Step 3: Poll Google's token endpoint until authorized
    token_url = "https://oauth2.googleapis.com/token"
    start_time = time.time()
    timeout = 300  # seconds

    while time.time() - start_time < timeout:
        time.sleep(interval)
        token_response = requests.post(
            token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )

        if token_response.status_code == 200:
            token_data = token_response.json()
            with open(TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            await send_message(user_id, "✅ Google Drive authentication successful.")
            return True
        
        error = token_response.json().get("error")

        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
            continue
        else:
            await send_message(user_id, f"❌ Authentication failed: {token_response.json().get('error_description', error)}")

    await send_message(user_id, "❌ Authentication timed out. Please try again.")
    return False