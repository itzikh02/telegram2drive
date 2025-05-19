import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from utils.bot_application import app
from utils.bot_utils import send_message, ask_user_input

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service(user_id: str = None):
    """
    Authenticates and returns a Google Drive API service instance.
    Requires 'credentials.json' to exist in the same directory.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES, redirect_uri='http://localhost:8080/')
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

            if user_id:
                send_message(user_id, "🔗 Please go to this URL and authorize access:")
                send_message(user_id, auth_url)
                code = ask_user_input(user_id, "📥 Paste the authorization code here:")
            else:
                print("🔗 Please go to this URL and authorize access:")
                print(auth_url)

            code = input("📥 Paste the authorization code here: ")

            flow.fetch_token(code=code)
            creds = flow.credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def upload_file_to_drive(file_path: str, file_name: str, folder_id: str = None):
    """
    Uploads a file to Google Drive.

    :param file_path: Path to the local file.
    :param file_name: Desired name in Google Drive.
    :param folder_id: Optional folder ID to upload into.
    :return: The uploaded file's ID.
    """
    service = get_drive_service()
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
