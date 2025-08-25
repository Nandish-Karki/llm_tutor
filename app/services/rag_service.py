# from chromadb import PersistentClient
# from chromadb.utils import embedding_functions

# # Setup
# client = PersistentClient(path="chroma_storage")
# embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# collection = client.get_or_create_collection("llm_tutor_docs", embedding_function=embed_fn)

# def retrieve_relevant_chunks(question: str, document_id: str, top_k: int = 5) -> list:
#     """
#     Retrieve the top-k most relevant chunks from ChromaDB using the question embedding.
#     """
#     results = collection.query(
#         query_texts=[question],
#         n_results=top_k,
#         where={"document_id": document_id}
#     )
    
#     docs = results.get("documents", [[]])[0]
#     metadatas = results.get("metadatas", [[]])[0]

#     return [{"text": doc, "module": meta["module"]} for doc, meta in zip(docs, metadatas)]
# rag_retriever.py
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

client = PersistentClient(path="chroma_storage")
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("llm_tutor_docs", embedding_function=embedder)

def retrieve_relevant_chunks(query, document_id, top_k=5):
    """
    Retrieve top_k most semantically relevant chunks from ChromaDB for a given query.
    Always returns top_k regardless of score.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"document_id": document_id}
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        print(f"[RAG DEBUG] Found {len(documents)} candidates for query: '{query}'")

        relevant_chunks = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            score = 1 - dist
            print(f"[RAG SCORE] Chunk (module {meta.get('module')}): {doc[:60]}... | Score: {score:.4f}")
            relevant_chunks.append({
                "chunk": doc,
                "module_number": meta.get("module"),
                "similarity_score": round(score, 4)
            })

        # Already sorted from ChromaDB by relevance, but re-sorting just in case
        return sorted(relevant_chunks, key=lambda x: x["similarity_score"], reverse=True)[:top_k]

    except Exception as e:
        print("Error during retrieval:", e)
        return []

