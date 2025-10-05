# llm_tutor

**A Retrieval-Augmented LLM-based tutor backend** — Flask API, document ingestion and chunking, vectorstore indexing (ChromaDB), and multi-model generation using Ollama (LLaMA family) + OpenAI. Designed to create learning modules from uploaded documents and answer module-specific questions with optional speech synthesis.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Quick Start (local)](#quick-start-local)
6. [Configuration / Environment Variables](#configuration--environment-variables)
7. [Document ingestion pipeline](#document-ingestion-pipeline)
8. [API Endpoints](#api-endpoints)
9. [Module generation & RAG flow](#module-generation--rag-flow)
10. [Speech synthesis (optional)](#speech-synthesis-optional)
11. [Testing](#testing)
12. [Deployment](#deployment)
13. [Contributing](#contributing)
14. [Troubleshooting](#troubleshooting)
15. [License & Credits](#license--credits)

---

## Project Overview

`llm_tutor` is a backend service that:

* Accepts documents (PDF, DOCX, PPTX, TXT),
* Extracts and chunks text, indexes chunks into a vector DB (ChromaDB),
* Generates learning module indexes and module content using LLMs (Ollama / LLaMA for module naming; OpenAI GPT-4o for final answers by default),
* Provides endpoints to fetch modules, module content, document references, and to post/retrieve notes,
* Optionally synthesizes spoken answers (e.g., AWS Polly integration).

This repository implements a RAG (Retrieval-Augmented Generation) pipeline and a small API to act as a tutor backend.

---

## Features

* Multi-format document parsing (PDF, DOCX, PPTX, plain text).
* Text chunking using `langchain.text_splitter.RecursiveCharacterTextSplitter`.
* Embeddings storage with ChromaDB (local or cloud).
* LLM orchestration: Ollama (LLaMA) for module naming and preliminary summarization; OpenAI GPT for final answer generation.
* Caching of generated module indexes in Firebase Firestore.
* Note-taking endpoints per document/module.
* Confidence & similarity scoring between original text and cleaned/generated text for evaluation.
* Extensible: swap LLM backends, change chunker, or swap vector DB.

---

## Architecture

```
[User] -> [Flask API] -> 
  - Upload endpoint -> [Parser (PyMuPDF / python-docx)] -> [Text Splitter] -> [ChromaDB]
  - Module index endpoint -> [ChromaDB search] -> [Ollama / LLaMA] -> (cache -> Firestore)
  - Question endpoint -> [ChromaDB retrieve top chunks] -> [RAG prompt] -> [GPT-4o / OpenAI] -> (Optional: Polly TTS)
  - Notes endpoint -> [Firestore]
```

---

## Prerequisites

* Python 3.10+ (3.11 recommended)
* Git
* (Optional) Docker (if you prefer containerized deployment)
* ChromaDB (local or cloud) — or compatible vectorstore
* Firebase project (Firestore + Cloud Storage) for metadata & file storage (optional but recommended)
* (Optional) Ollama server for running LLaMA models locally
* OpenAI API key (if using OpenAI for final answers)
* (Optional) AWS credentials for Polly TTS or any other TTS provider

Python packages (example):

```
flask
gunicorn
chromadb
langchain
pymupdf
python-docx
sentence-transformers
firebase-admin
requests
python-dotenv
boto3  # if using AWS Polly
```

---

## Quick Start (local)

1. Clone repo:

   ```bash
   git clone https://github.com/<your-username>/llm_tutor.git
   cd llm_tutor
   ```
2. Create and activate virtualenv:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows
   ```
3. Install requirements:

   ```bash
   pip install -r requirements.txt
   ```
4. Create `.env` with required env vars (see next section).
5. Run the Flask app:

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run
   ```

   Or using gunicorn in production:

   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

---

## Configuration / Environment Variables

Create a `.env` file (example keys):

```
# Firebase
FIREBASE_CREDENTIALS=/path/to/firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_HOST=   # if remote

# OpenAI
OPENAI_API_KEY=sk-...

# Ollama (if using)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama-3

# App
FLASK_ENV=development
SECRET_KEY=supersecret

# AWS Polly (optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-central-1
POLLY_VOICE=Joanna
```

> Note: Keep credentials secret. Use environment variables and a secrets manager in production.

---

## Document ingestion pipeline

1. **Upload**: Endpoint receives file and metadata; file stored (Cloud Storage / local `uploads/`).
2. **Parsing**:

   * PDFs: `PyMuPDF` (fast, reliable extraction)
   * DOCX: `python-docx`
   * PPTX: `python-pptx` or export to text
3. **Cleaning**: remove headers, footers, repeated artifacts, page numbers.
4. **Chunking**: `langchain.text_splitter.RecursiveCharacterTextSplitter` with overlap (e.g., chunk size 1000 chars, overlap 200).
5. **Embedding**: Use `sentence-transformers` or provider embeddings (OpenAI / HuggingFace) to embed chunks.
6. **Indexing**: Insert embeddings and metadata into ChromaDB with references to original doc/module/page.
7. **Module generation**:

   * A module index (module titles + short summaries) is suggested by LLaMA/Ollama using top chunks per chapter.
   * Cache results in Firestore to avoid repeated LLM calls.

---

## API Endpoints (example)

> These map to the endpoints you implemented earlier — adjust routes and payloads to match your code.

* `POST /upload`
  Upload a document. Request: file multipart + metadata. Response: documentId.

* `GET /documents/:documentId/modules`
  Get module index (cached or generated). Response: `[{moduleNumber, title, summary, startChunkId, confidence}]`

* `GET /documents/:documentId/modules/:moduleNumber/text`
  Returns assembled text for the module (from chunks), and optionally the cleaned + original passages.

* `GET /documents/:documentId/references?chapterNumber=`
  Get references/backlinks for a chapter/module.

* `POST /documents/:documentId/modules/:moduleNumber/ask`
  Ask a question using that module as context. Body: `{ question: "...", useTTS: false }`.
  Response: `{ answer: "...", sources: [...], audioUrl?: "..." }`

* `POST /documents/:documentId/modules/:moduleNumber/notes`
  Post a note tied to a module. Body: `{ userId, noteText }`. Stored in Firestore.

* `GET /documents/:documentId/modules/:moduleNumber/notes`
  Get notes for module.

---

## Module generation & RAG flow

* **Retrieve**: Search ChromaDB for top-N chunks based on the question or module context.
* **Construct prompt**: Combine system instructions (tutor persona), module context (concise), retrieved chunks, and the user question.
* **Call LLM**: Use OpenAI GPT-4o for final answer generation. You may use Ollama/LLaMA for draft answers or auxiliary tasks.
* **Post-process**: Attach citations (chunk ids or page numbers), compute similarity/confidence (cosine similarity + normalized scoring).
* **Optional TTS**: Send answer text to Polly (or other TTS) and return audio URL.

---

## Speech synthesis (optional)

Example uses AWS Polly:

* Configure `boto3` with AWS credentials.
* Call Polly to synthesize speech to MP3.
* Store MP3 in Cloud Storage / local `static/audio/` and return its URL.

---

## Testing

* Unit tests for:

  * Parser outputs (PDF/DOCX -> raw text).
  * Chunker: chunk sizes and overlaps.
  * Embedding + retrieval: embedding shape + nearest-neighbor sanity checks.
  * Endpoint tests using pytest + test client.
* Integration tests:

  * End-to-end upload -> module generation -> ask flow on a sample document.

---

## Deployment

**Options**:

* Docker container + Kubernetes (recommended for scale).
* Deploy Flask app behind a reverse proxy (NGINX) + gunicorn.
* Managed services: Render, Heroku (small scale), or AWS ECS/EKS.

**Docker (simple)**

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_APP=app.py
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

---

## Contributing

1. Fork the repo
2. Create a feature branch `git checkout -b feature/your-feature`
3. Commit changes, push, and open a PR
4. Add tests and documentation for major changes

Please follow standard commit message conventions and add clear descriptions for LLM prompt changes.

---

## Troubleshooting

* **Low-quality module titles**: tune the prompt used for module generation (provide examples and format constraints).
* **Missing chunks in retrieval**: check embedding model compatibility and normalized vector dimensions.
* **ChromaDB persistence issues**: ensure the `CHROMA_PERSIST_DIR` or remote Chroma config is reachable and writable.
* **Firestore permission errors**: confirm service account JSON and project ID in env vars.

---

## Notes / Recommendations

* Cache LLM outputs aggressively (module index, frequently asked questions).
* Track token usage and costs if using OpenAI for answers.
* Add rate-limiting on public endpoints.
* Consider user-level personalization (memory) — store small conversation contexts per user for continuity.

---

## License

Distributed under the MIT License. See `LICENSE` for details.

---

## Authors & Acknowledgements

* Maintainer: Nandish M. Karki
* Contributors: (add names)
* References:

  * LangChain, ChromaDB docs
  * PyMuPDF, python-docx
  * OpenAI & Ollama docs

---

## Contact

For questions, issues or contributions, open an issue or contact: `nandishkarki@gmail.com`

*— End of README —*
