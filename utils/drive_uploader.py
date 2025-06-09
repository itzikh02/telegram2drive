import os
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


from utils.bot_utils import send_message

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            token_data = json.load(token)

        with open("credentials.json") as f:
            client_info = json.load(f)["installed"]

        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_info["client_id"],
            client_secret=client_info.get("client_secret"),
            scopes=SCOPES
        )
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
