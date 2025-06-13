# Wasserstoff-AiInternTask
This repository contains the implementation of task assigned for wasserStoff AI internship
# Document Research & Theme QA System(chatbot)

This project is an AI-powered **Document QA System** that enables users to:

- Upload PDF, DOCX, TXT, MD, CSV, and scanned image documents  
- Automatically extract, chunk, and embed their content  
- Ask questions and receive answers with:
  -  **Per-document citations** (with page & paragraph)
  -  **Theme identification**
  - **Synthesized cross-document summaries**

It supports both **OpenAI** and **Groq** (e.g., LLaMA-3 via `llama3-70b-8192`).

---

## Features

-  Upload 75+ documents (PDF, text, DOCX, CSV, Markdown, image with OCR)
-  Document chunking + embedding via SentenceTransformers
-  Querying with LangChain `ChatOpenAI`
-  Theme-based structured answers
-  OCR fallback for scanned PDFs/images (via Tesseract)
-  Works with Groq (`llama3`) or OpenAI (`gpt-3.5`, `gpt-4`)
-  Streamlit frontend for upload + chat
-  FAISS vector store for fast retrieval

---

## 📦 Tech Stack

| Layer         | Tools Used                            |
|---------------|----------------------------------------|
| Backend API   | FastAPI                               |
| LLMs          | Groq (llama3), OpenAI (gpt-3.5-turbo) |
| Embeddings    | SentenceTransformers (`MiniLM-L6-v2`) |
| Vector Store  | FAISS                                 |
| OCR           | Tesseract + pdf2image + pdfplumber    |
| Frontend UI   | Streamlit                             |

---

## 🛠️ Setup Instructions

### 1. Clone and Install

```bash
git clone https://github.com/your-org/document-qa-chatbot.git
cd document-qa-chatbot/backend/app

python -m venv venv_bot
source venv_bot/bin/activate  # or venv_bot\Scripts\activate on Windows

pip install -r requirements.txt
```

### 2. Configure `.env`

```dotenv
LLM_PROVIDER=groq

GROQ_API_KEY=your-groq-key
GROQ_API_BASE=https://api.groq.com/openai/v1

OPENAI_API_KEY=your-openai-key  # optional
LLM_MODEL=llama3-70b-8192
LLM_TEMPERATURE=0.3
FASTAPI_ENV=development
```

### 3. Run FastAPI Server

```bash
uvicorn main:app --reload
```

Open in browser: http://127.0.0.1:8000/docs

---

## 🖼Streamlit Frontend

```bash
streamlit run frontend.py
```

---

## File Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── services/
│   │   ├── ocr.py
│   │   ├── query.py
│   │   ├── document_manager.py
│   │   ├── llm.py
│   │   ├── embedder.py
│   │   └── vector_store.py
├── data/
├── uploads/
```

---

##  API Overview

| Endpoint         | Method | Description                    |
|------------------|--------|--------------------------------|
| `/upload`        | POST   | Upload a single file           |
| `/upload-batch`  | POST   | Upload multiple files          |
| `/query`         | POST   | Ask question + get themes      |
| `/documents`     | GET    | List processed doc stats       |
| `/documents`     | DELETE | Clear all documents            |

---

## Output Format

```text
**Individual Document Responses:**
| Document ID | Extracted Answer | Citation |

**Theme Name:** Data Privacy Violations
Supporting Docs: Doc1 (Page 2, Para 3)
Summary: ...

**Synthesized Answer:** ...
```

---

## Sample Datasets

- `realistic_document_pack.zip` (.txt, .csv, .docx)
- `short_documents_pack.zip` (.pdf and OCR)

---

## Security Notes

- `.env` is ignored via `.gitignore`
- Logs and uploads excluded from versioning

---

