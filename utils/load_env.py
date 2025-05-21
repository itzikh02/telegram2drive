from dotenv import load_dotenv

import os

# Load .env
load_dotenv()

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = set(os.getenv("ALLOWED_USERS", "").split(","))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DOWNLOAD_DIR = "downloads"

# Check if .env is set and loaded correctly
def validate_env():
    required_env_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "ALLOWED_USERS": ALLOWED_USERS,
        "LOG_CHANNEL_ID": LOG_CHANNEL_ID,
        "DRIVE_FOLDER_ID": DRIVE_FOLDER_ID,
    }

    # Create the download directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    for name, value in required_env_vars.items():
        if not value:
            raise ValueError(f"{name} is not set in the .env file")
        

