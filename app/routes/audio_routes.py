from flask import Blueprint, request, jsonify
from app.services.audio_service import (
    get_cached_modules,
    generate_ssml,
    synthesize_audio_and_marks,
    save_module_audio
)
from app.utils.jwt_handler import verify_token
audio_bp = Blueprint("audio_routes", __name__)

@audio_bp.route("/generate-module-audio", methods=["POST"])
def generate_module_audio():
    try:
        auth_header = request.headers.get("Authorization", "")
        token = None
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        decoded = verify_token(token)
        user_email=decoded.get("email")
        data = request.json
        email = data.get("email")
        document_id = data.get("documentId")
        module_number = data.get("moduleNumber")

        if not all([user_email, document_id, module_number]):
            return jsonify({"error": "Missing required fields"}), 400

        try:
            module_number = int(module_number)
        except ValueError:
            return jsonify({"error": "Invalid module number format"}), 400

        modules = get_cached_modules(email, document_id)
        if not modules:
            return jsonify({"error": "No cached modules found"}), 404

        selected = next((m for m in modules if m["module_number"] == module_number), None)
        if not selected:
            return jsonify({"error": f"Module {module_number} not found"}), 404

        content = selected.get("module_content")
        
        ssml = generate_ssml(content, chunk_id=module_number)
        
        audio_path, speech_marks = synthesize_audio_and_marks(ssml, module_number)
        public_url = save_module_audio(email, document_id, module_number, ssml, audio_path, speech_marks)

        return jsonify({
            "message": f"Audio and SSML generated for module {module_number}",
            # "ssml": ssml,
            "audio_file": audio_path,
            "public_url": public_url,
            "speech_marks": speech_marks,
            "cleaned_text": content,  # ✅ Include cleaned module content here
            "module_name": selected.get("module_name", ""),
            "similarity": selected.get("similarity", 0.0),
            "confidence": selected.get("confidence", 0.0),
            "length": selected.get("length", 0),
            "cleaned_length": selected.get("cleaned_leangth", 0)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
