from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import uuid
from datetime import datetime

db = create_client(SUPABASE_URL, SUPABASE_KEY)

class DatabaseService:
    
    @staticmethod
    def create_user(user_id, username, referrer_id=None):
        """Create new user with referral tracking."""
        try:
            existing = db.table("users").select("*").eq("user_id", user_id).execute()
            if existing.data:
                return existing.data[0]
            
            referral_code = str(uuid.uuid4())[:8].upper()
            result = db.table("users").insert({
                "user_id": user_id,
                "username": username,
                "credits": 0,
                "referral_code": referral_code,
                "referrer_id": referrer_id,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    @staticmethod
    def get_user(user_id):
        """Fetch user by ID."""
        try:
            result = db.table("users").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    @staticmethod
    def add_credits(user_id, amount, reason):
        """Add credits to user."""
        try:
            user = DatabaseService.get_user(user_id)
            if not user:
                return False
            
            new_balance = user.get("credits", 0) + amount
            db.table("users").update({
                "credits": new_balance
            }).eq("user_id", user_id).execute()
            
            db.table("credit_transactions").insert({
                "user_id": user_id,
                "amount": amount,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            
            return True
        except Exception as e:
            print(f"Error adding credits: {e}")
            return False

    @staticmethod
    def deduct_credits(user_id, amount, reason):
        """Deduct credits from user (only if sufficient)."""
        try:
            user = DatabaseService.get_user(user_id)
            if not user or user.get("credits", 0) < amount:
                return False
            
            new_balance = user.get("credits", 0) - amount
            db.table("users").update({
                "credits": new_balance
            }).eq("user_id", user_id).execute()
            
            db.table("credit_transactions").insert({
                "user_id": user_id,
                "amount": -amount,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            
            return True
        except Exception as e:
            print(f"Error deducting credits: {e}")
            return False

    @staticmethod
    def save_lookup_history(user_id, lookup_type, search_query, search_id, credit_cost, status):
        """Save lookup history with minimal data."""
        try:
            db.table("lookup_history").insert({
                "user_id": user_id,
                "lookup_type": lookup_type,
                "search_query": search_query,
                "search_id": search_id,
                "credit_cost": credit_cost,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving lookup history: {e}")
            return False

    @staticmethod
    def create_payment_request(user_id, amount_credits, utr=None, screenshot_url=None):
        """Create manual payment request."""
        try:
            result = db.table("payment_requests").insert({
                "user_id": user_id,
                "credit_amount": amount_credits,
                "utr": utr,
                "screenshot_url": screenshot_url,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None

    @staticmethod
    def approve_payment(payment_id, credit_amount, user_id):
        """Approve payment and add credits."""
        try:
            db.table("payment_requests").update({
                "status": "approved"
            }).eq("id", payment_id).execute()
            
            DatabaseService.add_credits(user_id, credit_amount, f"Payment approved (ID: {payment_id})")
            return True
        except Exception as e:
            print(f"Error approving payment: {e}")
            return False

    @staticmethod
    def reject_payment(payment_id):
        """Reject payment request."""
        try:
            db.table("payment_requests").update({
                "status": "rejected"
            }).eq("id", payment_id).execute()
            return True
        except Exception as e:
            print(f"Error rejecting payment: {e}")
            return False

    @staticmethod
    def get_user_by_referral_code(referral_code):
        """Get user by referral code."""
        try:
            result = db.table("users").select("*").eq("referral_code", referral_code).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching by referral: {e}")
            return None

    @staticmethod
    def record_referral(referrer_id, referred_user_id, credit_reward):
        """Record successful referral."""
        try:
            db.table("referrals").insert({
                "referrer_id": referrer_id,
                "referred_user_id": referred_user_id,
                "credit_reward": credit_reward,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error recording referral: {e}")
            return False

