from dotenv import load_dotenv
import os

from telegram.ext import Application

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder() \
    .token(BOT_TOKEN) \
    .base_url("http://localhost:8081/bot") \
    .base_file_url("http://localhost:8081/file/") \
    .local_mode(True) \
    .build()