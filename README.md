# 📁 Telegram2Drive Bot

A Telegram bot that uses the **Telegram Local Bot API** to receive large files (1.5GB+) and uploads them to **Google Drive**.  
Built with `python-telegram-bot` and designed for privacy, performance, and flexibility.

---

## 🚀 Features

- ✅ Uses **Local Telegram Bot API** (for large file support & speed)
- 🔒 Accepts commands only from **authorized users**
- ☁️ Uploads received files to **Google Drive**
- 📋 Logs bot activity to a **Telegram channel**
- 🛠️ Modular and easy to expand

---

## 📆 Requirements

- Python 3.8+
- Local Telegram Bot API (compiled & running)
- Google Drive API credentials
- `venv` environment (recommended)

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/itzikh02/telegram2drive
cd telegram2drive
```

### 2. Create Virtual Environment & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup `.env` file

Create a file named `.env` in the root folder:

```env
BOT_TOKEN=your_bot_token
ALLOWED_USERS=123456789,987654321
LOG_CHANNEL_ID=-1001234567890
```

> 💡 `ALLOWED_USERS` should be a comma-separated list of Telegram user IDs.

### 4. Run the Bot

```bash
source venv/bin/activate
python3 bot.py
```

Or run it in the background with `screen`:

```bash
screen -S telegram2drive
source venv/bin/activate
python3 bot.py
```

---

## 🧪 Commands

- `/start` – Check if the bot is up and authorized
- `/ping` – Ping-pong test command

More commands and features coming soon...

---

## 💽 Local Bot API Setup

This bot is designed to work with Telegram's **Local Bot API** for handling large files.  
Make sure your local bot API server is running and accessible at `http://localhost:8081`.

> Check out [Telegram's GitHub page](https://github.com/tdlib/telegram-bot-api) for setup instructions.

---

## 📁 Project Structure

```
telegram2drive/
├── bot.py               # Main bot logic
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── venv/                # Virtual environment (optional)
```

---

## 🙌 Contributions

Pull requests are welcome. If you have suggestions or feature requests, feel free to open an issue!

---

## 📬 Contact

For questions, reach out or open a GitHub issue.

