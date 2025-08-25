from flask import Blueprint, request, jsonify
from app.utils.jwt_handler import verify_token
from app.services.index_service import get_resource_index
index_bp = Blueprint("index", __name__)

@index_bp.route("/get-index/<document_id>", methods=["GET"])
def get_index_ofdoc(document_id):
    auth_header = request.headers.get("Authorization", "")
    token = None
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = verify_token(token)
    user_email=decoded.get("email")
    

    result = get_resource_index(document_id, user_email)

    return result