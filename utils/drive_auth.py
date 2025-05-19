import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from utils.bot_utils import send_message

SCOPES = ['https://www.googleapis.com/auth/drive.file']
auth_flows = {}

TOKEN_PATH = 'token.pickle'

async def start_auth_conversation(user_id):
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token_file:
            creds = pickle.load(token_file)

        if creds and creds.valid:
            await send_message(user_id, "✅ You're already authenticated with Google Drive.")
            return

        elif creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'wb') as token_file:
                pickle.dump(creds, token_file)
            await send_message(user_id, "🔁 Your token was successfully refreshed.")
            return

    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    auth_flows[user_id] = flow

    await send_message(user_id, f"🔗 Please authorize access:\n{auth_url}\n\nThen paste the code here:")

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