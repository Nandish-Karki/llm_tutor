# from flask import request, jsonify
# from app.helpers.polly_helper import synthesize_speech
# from app.services.llm_service import generate_answer
# from app.config.firebase import db
# from app.services.audio_service import get_cached_modules
# def handle_question():
#     data = request.get_json()
#     question = data.get('question')
#     email = data.get("email")
#     document_id = data.get("documentId")
#     module_number = data.get("moduleNumber")
#     emotion = data.get('emotion', 'neutral')

#     try:
#         module_number = int(module_number)
#     except ValueError:
#         return jsonify({"error": "Invalid module number format"}), 400
    

#     modules = get_cached_modules(email, document_id)
#     if not modules:
#         return jsonify({"error": "No cached modules found"}), 404
#     selected = next((m for m in modules if m["module_number"] == module_number), None)

#     if not selected:
#         return jsonify({"error": f"Module {module_number} not found"}), 404

#     content = selected.get("module_content")

#     answer_data = generate_answer(question, content, emotion)
#     audio_url   = synthesize_speech(answer_data['answer'], emotion)

#     return jsonify({
#         "answer":            answer_data["answer"],
#         "supporting_texts":  answer_data.get("supporting_texts", []),
#         "emotion":           emotion,
#         "module_number":     module_number,
#         "module_name":       selected.get("module_name", ""),
#         "ssmlAudioURL":      audio_url
#     })

# from flask import request, jsonify
# from app.helpers.polly_helper import synthesize_speech
# from app.services.llm_service import generate_answer
# from app.services.audio_service import get_cached_modules
# from app.services.rag_service import retrieve_relevant_chunks

# def handle_question():
#     data = request.get_json()
#     question = data.get('question')
#     email = data.get("email")
#     document_id = data.get("documentId")
#     module_number = data.get("moduleNumber")  # Optional
#     emotion = data.get('emotion', 'neutral')
#     print('testing')
#     print(data)

#     # if not all([question, email, document_id]):
#     #     return jsonify({"error": "Missing required fields"}), 400

#     # try:
#     #     module_number = int(module_number) if module_number is not None else None
#     # except ValueError:
#     #     return jsonify({"error": "Invalid module number format"}), 400

#     # # ===============================
#     # #  MODE 1: Module-based Answering
#     # # ===============================
#     # if module_number is not None:
#     #     modules = get_cached_modules(email, document_id)
#     #     if not modules:
#     #         # Attempt to generate modules on-the-fly
#     #         from app.services.index_service import get_resource_index  # or wherever you defined it
#     #         try:
#     #             response = get_resource_index(document_id, email)
#     #             if response.status_code != 200:
#     #                 return jsonify({"error": "Failed to index document"}), 500
#     #             modules = response.get_json()["modules"]
#     #         except Exception as e:
#     #             return jsonify({"error": "Failed to load or generate modules", "details": str(e)}), 500


#     #     selected = next((m for m in modules if m["module_number"] == module_number), None)
#     #     if not selected:
#     #         return jsonify({"error": f"Module {module_number} not found"}), 404

#     #     content = selected.get("module_content")
#     #     answer_data = generate_answer(question, content, emotion)

#     #     return jsonify({
#     #         "answer":            answer_data["answer"],
#     #         "supporting_texts":  answer_data.get("supporting_texts", []),
#     #         "emotion":           emotion,
#     #         "mode":              "module",
#     #         "module_number":     module_number,
#     #         "module_name":       selected.get("module_name", ""),
#     #         "ssmlAudioURL":      synthesize_speech(answer_data["answer"], emotion)
#     #     })

#     # ===============================
#     # MODE 2: RAG-based Answering
#     # ===============================
#     chunks = retrieve_relevant_chunks(question, document_id, top_k=5)
#     if not chunks:
#         return jsonify({"error": "No relevant content found"}), 404

#     answer_data = generate_answer(question, chunks, emotion)
#     return jsonify({
#         "answer":            answer_data["answer"],
#         "supporting_texts":  answer_data.get("supporting_texts", []),
#         "emotion":           emotion,
#         "mode":              "rag",
#         "document_id":       document_id,
#         "ssmlAudioURL":      synthesize_speech(answer_data["answer"], emotion)
#     })
from flask import request, jsonify
from app.helpers.polly_helper import synthesize_speech
from app.services.llm_service import generate_answer
from app.services.rag_service import retrieve_relevant_chunks  # ✅ RAG retriever

def handle_question():
    data = request.get_json()
    question = data.get('question')
    email = data.get("email")
    document_id = data.get("documentId")
    emotion = data.get('emotion', 'neutral')
    print(data)
    # Input validation
    if not all([question, email, document_id]):
        return jsonify({"error": "Missing required fields"}), 400

    #  RAG: Retrieve top relevant chunks using ChromaDB
    relevant_chunks = retrieve_relevant_chunks(question, document_id, top_k=5)
    print(f"Retrieved {len(relevant_chunks)} relevant chunks")
    if not relevant_chunks:
        return jsonify({"error": "No relevant content found"}), 404

    #  Combine retrieved chunks for LLM input
    combined_context = "\n\n".join([c["chunk"] for c in relevant_chunks])

    #  Generate LLM-based answer
    answer_data = generate_answer(question, combined_context, emotion)

    #  Optional TTS
    # audio_url = synthesize_speech(answer_data["answer"], emotion)

    #  Return full response
    return jsonify({
        "answer": answer_data["answer"],
        "supporting_texts": answer_data.get("supporting_texts", []),
        "emotion": emotion,
        "mode": "rag",
        "document_id": document_id,
        "retrieved_chunks": relevant_chunks,  # Optional: remove this if you want a cleaner response
        # "ssmlAudioURL": audio_url
    })
