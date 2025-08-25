from flask import Blueprint, request, jsonify
from app.services import auth_service

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    return jsonify(auth_service.handle_register(request))

@auth_bp.route("/login", methods=["POST"])
def login():
    return jsonify(auth_service.handle_login(request))
