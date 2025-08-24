# 📤 Telegram to Google Drive Bot

A Telegram bot that receives files from authorized users, downloads them via the Telegram Local Bot API, stores them on the server, and uploads them to a designated Google Drive folder.

---

## ✅ Features

- Supports large files (>1.5GB) using the **Telegram Local Bot API**
- Authorizes only specific users based on `.env` configuration
- Sends log messages to a Telegram channel
- Saves files locally before uploading to Google Drive
- Uploads files to a specific Google Drive folder (using folder ID)

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/itzikh02/telegram2drive.git
cd telegram2drive
```

### 2. Create and activate a virtual environment

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Install required dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Setup

### 1. `.env` file

Create a `.env` file in the root directory:

```env
BOT_TOKEN=your_telegram_bot_token
ALLOWED_USERS=12345678,87654321
LOG_CHANNEL_ID=your_log_channel
DRIVE_FOLDER_ID=your_google_drive_folder_id
```

### 2. Google Drive API setup

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a project and enable the **Google Drive API**
- Create OAuth 2.0 credentials (Desktop app)
- Add your google account to the test users list
- Download the `credentials.json` file and place it in your project root folder

---

## 🚀 Running the Bot

Make sure the Telegram Local API is running and accessible (e.g. at `http://localhost:8081`), then:

```bash
source venv/bin/activate
python bot.py
```

---

## 📂 Project Structure

```
/telegram2drive
├── bot.py
├── LICENSE
├── README.md
├── credentials.json
├── requirements.txt
└── utils
    ├── auth_handler.py
    ├── auth_utils.py
    ├── bot_application.py
    ├── bot_utils.py
    ├── drive_uploader.py
    ├── file_handler.py
    └── load_env.py
```

---

## 📌 Notes

- The bot uses Telegram [**Local Bot API**](https://github.com/tdlib/telegram-bot-api), not the cloud-based API.
- You must run the local Telegram Bot API server separately.
- Files are first saved locally, then uploaded to Google Drive, and then cleaned up if needed.

---

## 📝 Bot Commands

- /start - Start the bot and check your permmisions for to the bot. without any the bot wont respond.
- /ping - Check if the bot is running
- /auth - Login with your Google Account and allow the bot to use your Google Drive

---

## ✨ Credits

Made with ❤️ by Itzik Hanan, and his best friend Mr. ChatGPT

