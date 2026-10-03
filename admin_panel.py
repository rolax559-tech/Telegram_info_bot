from flask import Flask, render_template_string, request, jsonify
from config import ADMIN_IDS, SUPABASE_URL, SUPABASE_KEY
from database import DatabaseService
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Simple auth check - implement proper auth in production
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
@admin_required
def admin_dashboard():
    try:
        users_result = DatabaseService.db.table("users").select("*", count="exact").execute()
        lookups_result = DatabaseService.db.table("lookup_history").select("*", count="exact").execute()
        payments_result = DatabaseService.db.table("payment_requests").select("*", count="exact").execute()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <style>
                body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
                .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #007bff; color: white; }}
            </style>
        </head>
        <body>
            <h1>Admin Panel</h1>
            <div class="card">
                <h2>Dashboard Statistics</h2>
                <p>Total Users: <span class="stat">{users_result.count if hasattr(users_result, 'count') else len(users_result.data)}</span></p>
                <p>Total Lookups: <span class="stat">{lookups_result.count if hasattr(lookups_result, 'count') else len(lookups_result.data)}</span></p>
                <p>Pending Payments: <span class="stat">{payments_result.count if hasattr(payments_result, 'count') else len(payments_result.data)}</span></p>
            </div>
            <div class="card">
                <h2>Quick Actions</h2>
                <button onclick="alert('View pending payments')">Approve Payments</button>
                <button onclick="alert('Send broadcast')">Send Broadcast</button>
                <button onclick="alert('Manage credits')">Manage User Credits</button>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    try:
        result = DatabaseService.db.table("users").select("*").execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/payments/pending", methods=["GET"])
@admin_required
def get_pending_payments():
    try:
        result = DatabaseService.db.table("payment_requests").select("*").eq("status", "pending").execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/payments/<payment_id>/approve", methods=["POST"])
@admin_required
def approve_payment(payment_id):
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        credit_amount = data.get("credit_amount")
        
        DatabaseService.approve_payment(payment_id, credit_amount, user_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/payments/<payment_id>/reject", methods=["POST"])
@admin_required
def reject_payment(payment_id):
    try:
        DatabaseService.reject_payment(payment_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Admin panel started on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
      
