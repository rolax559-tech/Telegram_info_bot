import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# API
USERS_LOOKUP_API_BASE_URL = os.getenv("USERS_LOOKUP_API_BASE_URL")
USERS_LOOKUP_API_KEY = os.getenv("USERS_LOOKUP_API_KEY")

# Payment
UPI_ID = os.getenv("UPI_ID")
UPI_QR_IMAGE_URL = os.getenv("UPI_QR_IMAGE_URL")

# Channels
FORCE_JOIN_CHANNEL_ID = int(os.getenv("FORCE_JOIN_CHANNEL_ID"))
BACKUP_CHANNEL_ID = int(os.getenv("BACKUP_CHANNEL_ID"))

# Bot Config
WELCOME_IMAGE_URL = os.getenv("WELCOME_IMAGE_URL")
REFERRAL_CREDIT_REWARD = int(os.getenv("REFERRAL_CREDIT_REWARD", 50))
MOBILE_LOOKUP_CREDIT_COST = int(os.getenv("MOBILE_LOOKUP_CREDIT_COST", 10))

