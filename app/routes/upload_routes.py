from flask import Blueprint, request, jsonify
from app.services.upload_service import (
    upload_document_to_firestore_storage,
    client,
    add_note,
    get_notes
)
from app.utils.jwt_handler import verify_token

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload-doc", methods=["POST"])
def upload():

    # 1. Extract Bearer token
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ", 1)[1]

    # 2. Pull file & metadata from form
    uploaded_file = request.files.get("file")
    document_name = request.form.get("documentName")

    # 3. Delegate to the service layer
    result, status_code = upload_document_to_firestore_storage(
        token,
        uploaded_file,
        document_name
    )

    # 4. Return JSON + HTTP status
    return jsonify(result), status_code

@upload_bp.route("/index/<document_id>", methods=["GET"])
def get_resource_index(document_id):
    # returns count of modules
    collection = client.get_collection(name="llm_tutor_docs")
    results = collection.get(where={"document_id": document_id})
    modules = []
    for doc, metadata in zip(results["documents"], results["metadatas"]):
        modules.append({
            "module": metadata["module"],
            "preview": doc[:100] + "..." if len(doc) > 100 else doc,
            "length": len(doc)
        })

    return jsonify({
        "moduleCount": len(results["documents"]),
        "modules": sorted(modules, key=lambda x: x["module"])
    })

@upload_bp.route("/module/<document_id>/<int:module_number>", methods=["GET"])
def get_module_text(document_id, module_number):
    collection = client.get_collection(name="llm_tutor_docs")
    result = collection.get(where={"document_id": document_id}, limit=1,
                            where_document={"$contains": f"{module_number}"})

    print(result)
    if not result["documents"]:
        return jsonify({"error": "Module not found"}), 404

    return jsonify({
        "module": module_number,
        "text": result["documents"][0],
        "length": len(result["documents"][0])
    })
def get_user_email_from_request():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = verify_token(token)
    return decoded.get("email")


@upload_bp.route("/notes/<document_id>/<int:chapter>", methods=["POST"])
def post_note(document_id, chapter):
    user_email = get_user_email_from_request()
    note_text = request.json.get("note")
    if not note_text:
        return jsonify({"error": "Missing 'note' in request body"}), 400
    add_note(document_id, chapter, note_text,user_email)
    return jsonify({"status": "success"})

@upload_bp.route("/notes/<document_id>/<int:chapter>", methods=["GET"])
def get_all_notes(document_id, chapter):
    user_email = get_user_email_from_request()
    notes = get_notes(document_id, chapter, user_email)
    return jsonify({"notes": notes})

