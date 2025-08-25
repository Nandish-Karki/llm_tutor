import uuid
import datetime
from flask import current_app
from app.config.firebase import db
from app.helpers.storage_helper import upload_file_to_storage
from app.helpers.upload_helpers import (
    is_resume_parsable,
    extract_text_from_pdf,
    extract_text_from_docx
)
from app.utils.jwt_handler import verify_token
from app.helpers.document_parser import download_and_read_file, chunk_text


# ChromaDB setup (Singleton client + consistent embedding function)
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

client = PersistentClient(path="chroma_storage")
chroma_embedder  = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("llm_tutor_docs", embedding_function=chroma_embedder)

# In-memory notes store


def upload_document_to_firestore_storage(token: str, file, document_name: str):
    """
    Verify token, validate & parse the file, upload to Cloud Storage,
    extract its text, index it, and record metadata in Firestore.

    Returns: (payload: dict, http_status: int)
    """
    # 1️ Auth
    decoded = verify_token(token)
    email = decoded.get("email")
    if not email:
        return {"status": "failure", "message": "Invalid token"}, 401

    # 2️ File presence & name
    if file is None or not getattr(file, "filename", ""):
        return {"status": "failure", "message": "No file provided"}, 400

    filename = file.filename
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext not in ("pdf", "docx"):
        return {"status": "failure", "message": "Only PDF or DOCX allowed"}, 400

    # 3️ Check name‐collision
    user_docs_col = db \
        .collection("documents") \
        .document(email) \
        .collection(document_name)
    existing = list(user_docs_col.limit(1).stream())
    if existing:
        return {
            "status":  "failure",
            "message": f"Document name '{document_name}' already exists"
        }, 409

    # 4️ Parsability
    file.stream.seek(0)
    if not is_resume_parsable(file.stream, filename):
        return {"status": "failure", "message": "Document is not parsable"}, 422

    # 5️ Extract text
    file.stream.seek(0)
    if ext == "pdf":
        extracted_text = extract_text_from_pdf(file.stream)
    else:
        extracted_text = extract_text_from_docx(file.stream)

    # 5. Upload binary to GCS
    file.stream.seek(0)
    doc_id = str(uuid.uuid4())
    # include doc_id in storage path so files won’t collide
    storage_folder = f"documents/{email}/{document_name}/{doc_id}"
    public_url, storage_path = upload_file_to_storage(
        file,
        filename,
        folder=storage_folder
    )

    # 6. Write metadata to Firestore
    doc_ref = db.document(storage_folder)
    doc_ref.set({
        "email":         email,
        "documentName":  document_name,
        "documentId":    doc_id,
        "filename":      filename,
        "url":           public_url,
        "storagePath":   storage_path,
        "extractedText": extracted_text,
        "uploadedAt":    datetime.datetime.utcnow()
    })

    # 7. Index into ChromaDB
    try:
        num_chunks = index_document(doc_id, public_url)
        print(f" Indexed {num_chunks} chunks for document ID: {doc_id}")
    except Exception as e:
        print("Error during indexing:", str(e))

    return {
        "status":      "success",
        "message":     "Document uploaded and indexed successfully",
        "documentUrl": public_url,
        "documentId":  doc_id
    }, 201


def index_document(document_id: str, document_url: str):
    """
    Download document, chunk text, and add to ChromaDB.
    """
    print(f"Indexing document ID: {document_id}")
    text = download_and_read_file(document_url)
    if not text:
        raise ValueError("No text extracted from document")

    chunks = chunk_text(text)
    print(f" {len(chunks)} chunks extracted")

    for idx, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas=[{"document_id": document_id, "module": idx}],
            ids=[f"{document_id}_{idx}"]
        )
    collection.persist()
    return len(chunks)


def add_note(document_id, module, note_text, user_email):
    doc_ref = db.collection("notes").document(f"{user_email}_{document_id}_{module}")
    doc = doc_ref.get()
    if doc.exists:
        notes = doc.to_dict().get("notes", [])
    else:
        notes = []
    notes.append(note_text)
    doc_ref.set({
        "notes": notes,
        "email": user_email,
        "documentId": document_id,
        "module": module
    })
    return {"status": "success", "message": "Note added"}

def get_notes(document_id, module, user_email):
    doc_ref = db.collection("notes").document(f"{user_email}_{document_id}_{module}")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("notes", [])
    return []
