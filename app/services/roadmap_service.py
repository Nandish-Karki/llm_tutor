from app.config.firebase import db
from app.utils.jwt_handler import verify_token

def save_roadmap_for_user(token: str, data: dict) -> tuple:
    decoded = verify_token(token)
    if not decoded or "email" not in decoded:
        return {"error": "Invalid or expired token"}, 401

    email = decoded["email"]
    document_name = data["documentName"]

    roadmap_payload = {
        "duration": data["duration"],
        "hoursPerDay": data["hoursPerDay"],
        "purpose": data["purpose"],
        "learningType": data["learningType"]
    }

    db.collection("roadmapRequirement") \
      .document(email) \
      .collection(document_name) \
      .document("info") \
      .set(roadmap_payload)

    return {"message": "Roadmap saved", "path": f"roadmapRequirement/{email}/{document_name}"}, 201
