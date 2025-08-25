from flask import jsonify
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from app.services.llm_service import call_llama_for_module_name
from app.config.firebase import db
from app.helpers.similarity_calculation import get_similarity_and_confidence
client = PersistentClient(path="chroma_storage")
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("llm_tutor_docs", embedding_function=embedder)
from app.helpers.text_cleaner import preprocess_uploaded_text

def get_resource_index(document_id, user_email):
    # 🔍 1. Check Firestore for cached modules
    doc_ref = db.collection("Indexes").document(user_email).collection(document_id).document("modules") 
    cached_doc = doc_ref.get()

    if cached_doc.exists and "modules" in cached_doc.to_dict():
        print("[CACHE HIT] Returning precomputed modules")
        cached_modules = cached_doc.to_dict()["modules"]
        return jsonify({
            "moduleCount": len(cached_modules),
            "modules": sorted(cached_modules, key=lambda x: x["module_number"])
        })

    # ⚙️ 2. If not cached, compute via Chroma and LLM
    print("[CACHE MISS] Generating modules from Chroma and LLM")
    collection = client.get_collection(name="llm_tutor_docs")
    results = collection.get(where={"document_id": document_id})
    modules = []





    for doc, metadata in zip(results["documents"], results["metadatas"]):
        module_name = call_llama_for_module_name(doc[:50])
        cleaned_text = preprocess_uploaded_text(doc)
        similarity, confidence = get_similarity_and_confidence(doc, cleaned_text)
        module_info = {
            "module_number": metadata["module"],
            "module_name": module_name,
            "module_content" : cleaned_text,
            "preview": doc[:100],
            "similarity" : similarity,
            "confidence" : confidence,
            "length": len(doc),
            "cleaned_leangth" : len(cleaned_text)
        }
        modules.append(module_info)

    # 💾 3. Store in Firestore
    doc_ref.set({ "modules": modules })

    return jsonify({
        "moduleCount": len(modules),
        "modules": sorted(modules, key=lambda x: x["module_number"])
    })
