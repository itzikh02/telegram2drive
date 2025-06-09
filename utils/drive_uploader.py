import os
import pickle

from telegram import Update
from telegram.ext import ContextTypes

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from utils.bot_utils import send_message
from utils.auth_utils import require_auth

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

@require_auth
def get_drive_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    else:
        raise Exception("🚫 No valid token found. Run /auth to authenticate.")

    return build('drive', 'v3', credentials=creds)


def upload_file_to_drive(file_path: str, file_name: str, folder_id: str = None):
    """
    Uploads a file to Google Drive.

    :param file_path: Path to the local file.
    :param file_name: Desired name in Google Drive.
    :param folder_id: Optional folder ID to upload into.
    :return: The uploaded file's ID.
    """
    service = get_drive_service(None, None)  # Update with actual update and context if needed
    file_metadata = {'name': file_name}

    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f"✅ File uploaded to Google Drive. File ID: {file.get('id')}")

    # Remove the file from download directory after uploading
    os.remove(file_path)

    return file.get('id')
