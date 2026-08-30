import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHANNEL_ID = os.getenv("ADMIN_CHANNEL_ID")
CARD_NUMBER = os.getenv("CARD_NUMBER")
CARD_HOLDER = os.getenv("CARD_HOLDER")
