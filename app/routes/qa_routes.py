from flask import Blueprint
from app.services.qa_service import handle_question

qa_bp = Blueprint('qa', __name__)

# POST /api/module/ask-question
@qa_bp.route('/ask-question', methods=['POST'])
def ask_question():
    return handle_question()
