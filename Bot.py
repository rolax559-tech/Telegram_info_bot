import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ChatAction
from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, MOBILE_LOOKUP_CREDIT_COST, BACKUP_CHANNEL_ID, REFERRAL_CREDIT_REWARD
from database import DatabaseService
from api_service import UsersLookupAPI
from utils import create_main_keyboard, create_admin_keyboard, format_lookup_result, is_admin, validate_mobile

api = UsersLookupAPI()

# Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user is new
    existing_user = DatabaseService.get_user(user.id)
    referrer_id = None
    
    # Check if started with referral code
    if context.args and len(context.args) > 0:
        ref_code = context.args[0]
        referrer = DatabaseService.get_user_by_referral_code(ref_code)
        if referrer:
            referrer_id = referrer["user_id"]
    
    if not existing_user:
        DatabaseService.create_user(user.id, user.username, referrer_id)
        
        # Record referral if applicable
        if referrer_id:
            DatabaseService.record_referral(referrer_id, user.id, REFERRAL_CREDIT_REWARD)
            DatabaseService.add_credits(referrer_id, REFERRAL_CREDIT_REWARD, f"Referral from {user.username}")
    
    welcome_text = f"Welcome {user.first_name}! 👋\n\nUse this bot to lookup user information.\n\nSelect an option below:"
    await update.message.reply_text(welcome_text, reply_markup=create_main_keyboard())

async def handle_mobile_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mobile lookup callback."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_data = DatabaseService.get_user(user.id)
    
    if not user_data:
        await query.edit_message_text("❌ User not found. Use /start")
        return
    
    if user_data.get("credits", 0) < MOBILE_LOOKUP_CREDIT_COST:
        await query.edit_message_text(
            f"❌ Insufficient credits.\n"
            f"You have: {user_data.get('credits', 0)}\n"
            f"Required: {MOBILE_LOOKUP_CREDIT_COST}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy Credits", callback_data="buy_credits")]])
        )
        return
    
    await query.edit_message_text("📱 Enter mobile number (10-13 digits):")
    context.user_data["mode"] = "mobile_lookup"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    user = update.effective_user
    message_text = update.message.text.strip()
    
    mode = context.user_data.get("mode")
    
    if mode == "mobile_lookup":
        if not validate_mobile(message_text):
            await update.message.reply_text("❌ Invalid mobile. Must be 10-13 digits.")
            return
        
        user_data = DatabaseService.get_user(user.id)
        if not user_data or user_data.get("credits", 0) < MOBILE_LOOKUP_CREDIT_COST:
            await update.message.reply_text("❌ Insufficient credits.")
            context.user_data["mode"] = None
            return
        
        await update.message.chat.send_action(ChatAction.TYPING)
        
        result = await api.mobile_lookup(message_text)
        
        if result["success"]:
            # Deduct credits
            DatabaseService.deduct_credits(user.id, MOBILE_LOOKUP_CREDIT_COST, f"Mobile lookup: {message_text}")
            
            # Save history
            DatabaseService.save_lookup_history(
                user.id,
                "mobile",
                message_text,
                result["search_id"],
                MOBILE_LOOKUP_CREDIT_COST,
                "success"
            )
            
            # Send backup to channel
            backup_text = f"🔍 Lookup Record\n"
            backup_text += f"User: {user.first_name} (ID: {user.id})\n"
            backup_text += f"Search ID: {result['search_id']}\n"
            backup_text += f"Type: Mobile Lookup\n"
            backup_text += f"Query: {message_text}\n"
            backup_text += f"Status: Success\n"
            backup_text += f"---\n"
            backup_text += format_lookup_result(result)
            
            try:
                await context.bot.send_message(BACKUP_CHANNEL_ID, backup_text)
            except Exception as e:
                print(f"Error sending backup: {e}")
            
            formatted = format_lookup_result(result)
            await update.message.reply_text(formatted, reply_markup=create_main_keyboard())
        else:
            DatabaseService.save_lookup_history(
                user.id,
                "mobile",
                message_text,
                result["search_id"],
                0,
                "failed"
            )
            await update.message.reply_text(
                f"❌ {result['error']}",
                reply_markup=create_main_keyboard()
            )
        
        context.user_data["mode"] = None

async def handle_buy_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy credits callback."""
    query = update.callback_query
    await query.answer()
    
    text = "💳 Buy Credits\n\nEnter number of credits you want to buy:\n(Type a number, e.g., 100)"
    await query.edit_message_text(text)
    context.user_data["mode"] = "buy_credits_input"

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile callback."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_data = DatabaseService.get_user(user.id)
    
    if not user_data:
        await query.edit_message_text("❌ User not found.")
        return
    
    text = f"👤 Your Profile\n\n"
    text += f"User ID: {user_data['user_id']}\n"
    text += f"Username: {user_data.get('username', 'N/A')}\n"
    text += f"Credits: {user_data.get('credits', 0)}\n"
    text += f"Referral Code: {user_data.get('referral_code', 'N/A')}\n"
    text += f"Joined: {user_data.get('created_at', 'N/A')}\n"
    
    await query.edit_message_text(text, reply_markup=create_main_keyboard())

async def handle_refer_earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle refer & earn callback."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_data = DatabaseService.get_user(user.id)
    
    if not user_data:
        await query.edit_message_text("❌ User not found.")
        return
    
    ref_code = user_data.get("referral_code", "N/A")
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={ref_code}"
    
    text = f"👥 Refer & Earn\n\n"
    text += f"Share your referral link:\n\n"
    text += f"`{ref_link}`\n\n"
    text += f"You earn {REFERRAL_CREDIT_REWARD} credits per successful referral!"
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=create_main_keyboard())

async def handle_lookup_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lookup history callback."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        result = DatabaseService.db.table("lookup_history").select("*").eq("user_id", user.id).order("timestamp", desc=True).limit(10).execute()
        history = result.data if result.data else []
        
        if not history:
            await query.edit_message_text("📜 No lookup history yet.", reply_markup=create_main_keyboard())
            return
        
        text = "📜 Your Recent Lookups (Last 10):\n\n"
        for h in history:
            text += f"🔍 {h.get('lookup_type', 'N/A').upper()}\n"
            text += f"   Query: {h.get('search_query', 'N/A')}\n"
            text += f"   ID: {h.get('search_id', 'N/A')}\n"
            text += f"   Status: {h.get('status', 'N/A')}\n"
            text += f"   Time: {h.get('timestamp', 'N/A')}\n\n"
        
        await query.edit_message_text(text, reply_markup=create_main_keyboard())
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}", reply_markup=create_main_keyboard())

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route callback queries."""
    query = update.callback_query
    data = query.data
    
    if data == "mobile_lookup":
        await handle_mobile_lookup(update, context)
    elif data == "buy_credits":
        await handle_buy_credits(update, context)
    elif data == "profile":
        await handle_profile(update, context)
    elif data == "refer_earn":
        await handle_refer_earn(update, context)
    elif data == "lookup_history":
        await handle_lookup_history(update, context)
    elif data == "admin_lookups" and is_admin(update.effective_user.id):
        await handle_admin_lookups(update, context)
    elif data == "admin_users" and is_admin(update.effective_user.id):
        await handle_admin_users(update, context)
    elif data == "admin_payments" and is_admin(update.effective_user.id):
        await handle_admin_payments(update, context)
    elif data == "admin_broadcast" and is_admin(update.effective_user.id):
        await handle_admin_broadcast(update, context)
    elif data == "admin_stats" and is_admin(update.effective_user.id):
        await handle_admin_stats(update, context)

async def handle_admin_lookups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin lookup config."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⚙️ Lookup Configuration\n\n"
        "Mobile Lookup - Cost: 10 credits\n"
        "ID Search - Coming Soon\n\n"
        "(Configure via environment variables)",
        reply_markup=create_admin_keyboard()
    )

async def handle_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin user management."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👤 Manage Users\n\n"
        "Feature: Manage user credits, view profiles\n"
        "(Database interface required)",
        reply_markup=create_admin_keyboard()
    )

async def handle_admin_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin payment approvals."""
    query = update.callback_query
    await query.answer()
    
    try:
        result = DatabaseService.db.table("payment_requests").select("*").eq("status", "pending").execute()
        payments = result.data if result.data else []
        
        if not payments:
            await query.edit_message_text("✅ No pending payments.", reply_markup=create_admin_keyboard())
            return
        
        text = f"💰 Pending Payment Requests ({len(payments)}):\n\n"
        for p in payments:
            text += f"ID: {p.get('id', 'N/A')}\n"
            text += f"User: {p.get('user_id', 'N/A')}\n"
            text += f"Credits: {p.get('credit_amount', 'N/A')}\n"
            text += f"UTR: {p.get('utr', 'N/A')}\n"
            text += f"---\n"
        
        await query.edit_message_text(text, reply_markup=create_admin_keyboard())
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}", reply_markup=create_admin_keyboard())

async def handle_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin broadcast."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📢 Broadcast Message\n\n"
        "Send a message to all users:\n"
        "(Type your message)",
        reply_markup=create_admin_keyboard()
    )
    context.user_data["mode"] = "admin_broadcast"

async def handle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin statistics."""
    query = update.callback_query
    await query.answer()
    
    try:
        users = DatabaseService.db.table("users").select("*", count="exact").execute()
        lookups = DatabaseService.db.table("lookup_history").select("*", count="exact").execute()
        payments = DatabaseService.db.table("payment_requests").select("*", count="exact").execute()
        
        api_health, api_msg = await api.health_check()
        
        text = "📊 System Statistics\n\n"
        text += f"👥 Total Users: {users.count if hasattr(users, 'count') else len(users.data)}\n"
        text += f"🔍 Total Lookups: {lookups.count if hasattr(lookups, 'count') else len(lookups.data)}\n"
        text += f"💳 Total Payments: {payments.count if hasattr(payments, 'count') else len(payments.data)}\n"
        text += f"🔌 API Status: {'✅ OK' if api_health else f'❌ {api_msg}'}\n"
        
        await query.edit_message_text(text, reply_markup=create_admin_keyboard())
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}", reply_markup=create_admin_keyboard())

def main():
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", lambda u, c: u.message.reply_text("Admin panel:", reply_markup=create_admin_keyboard()) if is_admin(u.effective_user.id) else None))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Start bot
    print("🚀 Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
  
