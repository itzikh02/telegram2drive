
from telegram.ext import CommandHandler

from utils.auth_utils import auth_start

auth_conv_handler = CommandHandler("auth", auth_start)
