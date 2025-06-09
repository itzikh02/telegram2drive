import os
import asyncio

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ContextTypes
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

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
            try:
                service = build("drive", "v3", credentials=creds)
                service.files().list(pageSize=1).execute()
                return True
            except Exception as e:
                if os.path.exists(TOKEN_PATH):
                    os.remove(TOKEN_PATH)
                    await log_to_channel("🧨 Access token appeared valid but was rejected by API. Token file deleted.")
                await log_to_channel("🧨 Access token appeared valid but failed API call. Token deleted.")
                return False

        # Refresh if token is expired and refresh_token exists
        # This will also catch cases where the refresh_token was revoked
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                updated_token_data = {
                    "access_token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "scope": scope,
                    "token_type": "Bearer",
                    "expiry": creds.expiry.isoformat() if creds.expiry else None,
                }
                with open(TOKEN_PATH, 'w') as token_file:
                    json.dump(updated_token_data, token_file)
            except RefreshError as e:
                if "invalid_grant" in str(e):
                    if os.path.exists(TOKEN_PATH):
                        os.remove(TOKEN_PATH)
                        await log_to_channel("🧨 Refresh token invalid or revoked. Token file deleted.")
                    await log_to_channel("🧨 Auth token was invalid or revoked. Token file was deleted.")
                return False
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

import asyncio
import time
import json
import requests
from telegram import Update
from telegram.ext import ContextTypes

from utils.bot_utils import send_message
from utils.auth_utils import authorized_only, check_auth, TOKEN_PATH

@authorized_only
async def auth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if await check_auth():
        await send_message(user_id, "🔐 You are already authenticated.")
        return True

    with open("credentials.json") as f:
        client_info = json.load(f)["installed"]

    client_id = client_info["client_id"]
    client_secret = client_info.get("client_secret")  # Optional for installed apps

    scope = "https://www.googleapis.com/auth/drive.file"

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
    timeout = 300

    await update.message.reply_text(
        f"🔐 To authorize the bot to access your Google Drive:\n\n"
        f"1. Go to: {verification_url}\n"
        f"2. Enter the code: `{user_code}`\n\n"
        f"The bot will wait until you complete the authorization.",
        parse_mode="Markdown"
    )

    asyncio.create_task(
        poll_for_token(user_id, client_id, client_secret, device_code, interval, timeout, update)
    )

async def poll_for_token(user_id, client_id, client_secret, device_code, interval, timeout, update):
    token_url = "https://oauth2.googleapis.com/token"
    start_time = time.time()

    while time.time() - start_time < timeout:
        await asyncio.sleep(interval)

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
            return False

    await update.message.reply_text(
        "❌ Authentication timed out. Please try again.\nYou can restart with /auth"
    )
    return False