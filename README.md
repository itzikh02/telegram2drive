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
python3 -m venv venv
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
LOG_CHANNEL_ID=@your_log_channel
DRIVE_FOLDER_ID=your_google_drive_folder_id
```

### 2. Google Drive API setup

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a project and enable the **Google Drive API**
- Create OAuth 2.0 credentials (Desktop app)
- Add your google account to the test users list
- Download the `credentials.json` file and place it in your project root
- On first run, you’ll be prompted to authorize and generate `token.pickle`

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
telegram2drive/
├── bot.py                 # Main bot script
├── drive_uploader.py      # Google Drive upload logic
├── requirements.txt       # Required Python packages
├── .env                   # Environment variables
├── credentials.json       # Google OAuth credentials
└── downloads/             # Local folder for saving files
```

---

## 📌 Notes

- The bot uses Telegram **Local Bot API**, not the cloud-based API.
- You must run the local Telegram Bot API server separately.
- Files are first saved locally, then uploaded to Google Drive, and then cleaned up if needed.

---

## ✨ Credits

Made with ❤️ by Itzik Hanan, and his best friend Mr. ChatGPT

