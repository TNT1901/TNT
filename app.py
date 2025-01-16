from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import time

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# Helper Functions
def get_user_data(user_id):
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    return user.to_dict() if user.exists else None

def update_user_data(user_id, data):
    user_ref = db.collection('users').document(user_id)
    user_ref.set(data, merge=True)

# Routes
@app.route("/checkin", methods=["POST"])
def checkin():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = get_user_data(user_id)

    if not user:
        # Initialize user data if not exists
        user = {"points": 0, "last_checkin": 0, "premium": False}

    current_time = int(time.time())
    if current_time - user.get("last_checkin", 0) < 3 * 60 * 60:
        return jsonify({"error": "Check-in allowed every 3 hours"}), 400

    # Update user points and last check-in time
    user["points"] += 10
    user["last_checkin"] = current_time
    update_user_data(user_id, user)

    return jsonify({"message": "Check-in successful", "points": user["points"]})

@app.route("/profile", methods=["GET"])
def profile():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = get_user_data(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user)

@app.route("/invite", methods=["POST"])
def invite():
    data = request.json
    user_id = data.get("user_id")
    referral_id = data.get("referral_id")

    if not user_id or not referral_id:
        return jsonify({"error": "User ID and Referral ID are required"}), 400

    user = get_user_data(user_id)
    referrer = get_user_data(referral_id)

    if not user:
        user = {"points": 0, "last_checkin": 0, "premium": False}
        update_user_data(user_id, user)

    if referrer:
        referrer["points"] += 20
        update_user_data(referral_id, referrer)

    return jsonify({"message": "Referral successful", "referrer_points": referrer["points"] if referrer else 0})

@app.route("/buy-premium", methods=["POST"])
def buy_premium():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = get_user_data(user_id)

    if not user:
        user = {"points": 0, "last_checkin": 0, "premium": False}

    user["premium"] = True
    update_user_data(user_id, user)

    return jsonify({"message": "Premium purchased successfully", "premium": True})

if __name__ == "__main__":
    app.run(debug=True)
