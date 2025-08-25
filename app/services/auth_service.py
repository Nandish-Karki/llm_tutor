import bcrypt
from firebase_admin import firestore
from app.config.firebase import db
from app.utils.jwt_handler import generate_token

def handle_register(request):
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]
        full_name = data["full_name"]

        existing = db.collection("users") \
                     .where("email", "==", email) \
                     .limit(1) \
                     .stream()
        if any(existing):
            return {
                "status":  "failure",
                "message": "Email already registered"
            }, 409

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user_doc = {
            "email": email,
            "full_name": full_name,
            "password": hashed_pw,
            "created_at": firestore.SERVER_TIMESTAMP
        }

        doc_ref = db.collection("users").document()
        doc_ref.set(user_doc)

        token = generate_token({"uid": doc_ref.id, "email": email})
        return {"uid": doc_ref.id, "email": email, "access_token": token}
    except Exception as e:
        return {"error": str(e)}

def handle_login(request):
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]

        users = db.collection("users").where("email", "==", email).limit(1).stream()
        for doc in users:
            user = doc.to_dict()
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                token = generate_token({"uid": doc.id, "email": email})
                return {"uid": doc.id, "email": email, "access_token": token}
            else:
                return {"error": "Invalid password"}

        return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}
