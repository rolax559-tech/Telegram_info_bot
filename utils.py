from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
import re

def create_main_keyboard():
    """Main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔍 Mobile Lookup", callback_data="mobile_lookup")],
        [InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer_earn")],
        [InlineKeyboardButton("📜 History", callback_data="lookup_history")],
        [InlineKeyboardButton("ℹ️ Profile", callback_data="profile")],
        [InlineKeyboardButton("📞 Support", url="https://t.me/support_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_admin_keyboard():
    """Admin panel keyboard."""
    keyboard = [
        [InlineKeyboardButton("⚙️ Lookup Config", callback_data="admin_lookups")],
        [InlineKeyboardButton("👤 Manage Users", callback_data="admin_users")],
        [InlineKeyboardButton("💰 Payment Approvals", callback_data="admin_payments")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🔐 Support Admins", callback_data="admin_support")],
    ]
    return InlineKeyboardMarkup(keyboard)

def format_lookup_result(api_response):
    """Format API response for Telegram display."""
    if not api_response.get("success"):
        return f"❌ Error: {api_response.get('error', 'Unknown error')}"
    
    data = api_response.get("data", {})
    search_id = api_response.get("search_id", "N/A")
    results = data.get("results", [])
    count = data.get("count", 0)
    
    output = f"🔍 Lookup Result (ID: {search_id})\n\n"
    output += f"Records found: {count}\n\n"
    
    for i, record in enumerate(results, 1):
        output += f"📋 Record {i}:\n"
        output += f"  📱 Mobile: {record.get('mobile', 'N/A')}\n"
        output += f"  👤 Name: {record.get('name', 'N/A')}\n"
        output += f"  👨‍👩‍👧 Father: {record.get('fname', 'N/A')}\n"
        output += f"  🏠 Address: {record.get('address', 'N/A')}\n"
        output += f"  📞 Alt: {record.get('alt', 'N/A')}\n"
        output += f"  🗺️ Circle: {record.get('circle', 'N/A')}\n"
        output += f"  🆔 ID: {record.get('id', 'N/A')}\n"
        if i < count:
            output += "\n---\n\n"
    
    return output

def is_admin(user_id):
    """Check if user is admin."""
    return user_id in ADMIN_IDS

def validate_mobile(mobile):
    """Validate mobile number format."""
    mobile = str(mobile).strip()
    return mobile.isdigit() and 10 <= len(mobile) <= 13
  
