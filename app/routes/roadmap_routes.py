from flask import Blueprint, request, jsonify
from app.services.roadmap_service import save_roadmap_for_user

roadmap_bp = Blueprint("roadmap", __name__)

@roadmap_bp.route("/save-roadmap", methods=["POST"])
def save_roadmap():
    # 1. Extract Bearer token
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ", 1)[1]

    # 2. Extract payload
    data = request.get_json(force=True)
    required = ["documentName", "duration", "hoursPerDay", "purpose", "learningType"]
    missing = [key for key in required if key not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # 3. Call service
    result, status_code = save_roadmap_for_user(token, data)

    # 4. Respond
    return jsonify(result), status_code
