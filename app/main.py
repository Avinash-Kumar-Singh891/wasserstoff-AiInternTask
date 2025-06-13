# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
import shutil
from pathlib import Path
import logging
import uuid
from services.document_manager import DocumentManager
from services.query import QueryProcessor
from config import config

logging.basicConfig(level=config.LOG_LEVEL,format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Research & Theme Identification API",
    description="Upload documents and query them with AI-powered theme identification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#global instances
doc_manager = DocumentManager()
query_processor = QueryProcessor()

#share the same vector store instance
query_processor.vector_store = doc_manager.vector_store

#pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    max_results: Optional[int] = 10
    include_metadata: Optional[bool] = True

class QueryResponse(BaseModel):
    question: str
    individual_answers: List[dict]
    themes: List[dict]
    synthesized_answer: str
    total_documents_searched: int
    processing_time: Optional[float] = None

class UploadResponse(BaseModel):
    status: str
    message: str
    document_id: str
    chunks_processed: int
    total_documents: int
    total_chunks: int

class DocumentStats(BaseModel):
    total_documents: int
    total_chunks: int
    documents: dict

#this is added to present the initial logs in the system  
@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    logger.info("Starting Document QA System...")
    
    # Validate configuration
    try:
        config.validate_config()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # load th
    try:
        if doc_manager.load_vector_store(config.FAISS_INDEX_PATH):
            stats = doc_manager.get_document_stats()
            logger.info(f"Loaded existing vector store with {stats['total_documents']} documents")
        else:
            logger.info("No existing vector store found, starting fresh")
    except Exception as e:
        logger.warning(f"Could not load vector store: {e}")

# Shutdown logs 
@app.on_event("shutdown")
async def shutdown_event():
    """Save vector store on shutdown"""
    try:
        doc_manager.save_vector_store(config.FAISS_INDEX_PATH)
        logger.info("Vector store saved successfully")
    except Exception as e:
        logger.error(f"Error saving vector store: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    stats = doc_manager.get_document_stats()
    return {
        "status": "healthy",
        "message": "Document QA System is running",
        "documents_loaded": stats['total_documents'],
        "total_chunks": stats['total_chunks']
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_id: Optional[str] = Form(None)
):
    """Upload and process a single document"""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not supported. Allowed: {config.ALLOWED_EXTENSIONS}"
        )
    
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size ({file_size} bytes) exceeds maximum ({config.MAX_FILE_SIZE} bytes)"
        )

    if not doc_id:
        doc_id = f"{Path(file.filename).stem}_{uuid.uuid4().hex[:8]}"

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
 
        logger.info(f"Processing document: {file.filename} (ID: {doc_id})")
        chunks_processed = doc_manager.upload_and_process_document(temp_file_path, doc_id)

        background_tasks.add_task(save_vector_store_background)

        stats = doc_manager.get_document_stats()
        
        logger.info(f"Successfully processed {file.filename}: {chunks_processed} chunks")
        
        return UploadResponse(
            status="success",
            message=f"Document '{file.filename}' processed successfully",
            document_id=doc_id,
            chunks_processed=chunks_processed,
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks']
        )
        
    except Exception as e:
        logger.error(f"Error processing document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.post("/upload-batch")
async def upload_batch_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload and process multiple documents"""
    
    if len(files) > 50:  # Reasonable batch limit
        raise HTTPException(status_code=400, detail="Too many files. Maximum 50 files per batch")
    
    results = []
    temp_files = []
    
    try:
      
        for file in files:
            if not file.filename:
                continue
                
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in config.ALLOWED_EXTENSIONS:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Unsupported file type: {file_ext}"
                })
                continue
            
            # Save temporarily
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(content)
                temp_files.append(temp_file.name)
                
                try:
                    doc_id = f"{Path(file.filename).stem}_{uuid.uuid4().hex[:8]}"
                    chunks_processed = doc_manager.upload_and_process_document(temp_file.name, doc_id)
                    
                    results.append({
                        "filename": file.filename,
                        "document_id": doc_id,
                        "status": "success",
                        "chunks_processed": chunks_processed
                    })
                    
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": str(e)
                    })
        background_tasks.add_task(save_vector_store_background)

        stats = doc_manager.get_document_stats()
        
        return {
            "status": "completed",
            "results": results,
            "total_documents": stats['total_documents'],
            "total_chunks": stats['total_chunks']
        }
        
    finally:
        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents with theme identification"""
    
    # Validate query
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(request.question) > config.MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Question too long. Maximum {config.MAX_QUERY_LENGTH} characters"
        )
    
    # Check if any documents are loaded
    stats = doc_manager.get_document_stats()
    if stats['total_documents'] == 0:
        raise HTTPException(status_code=400, detail="No documents loaded. Please upload documents first")
    
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Processing query: {request.question[:100]}...")
        
        # Process query
        results = query_processor.process_query(
            request.question, 
            k=min(request.max_results, config.MAX_CHUNKS_PER_QUERY)
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Query processed in {processing_time:.2f}s, found {len(results['individual_answers'])} matches")
        
        return QueryResponse(
            question=request.question,
            individual_answers=results['individual_answers'],
            themes=results['themes'],
            synthesized_answer=results['synthesized_answer'],
            total_documents_searched=stats['total_documents'],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")



@app.get("/documents", response_model=DocumentStats)
async def get_document_stats():
    """Get statistics about loaded documents"""
    return doc_manager.get_document_stats()


@app.delete("/documents")
async def clear_all_documents():
    """Clear all documents from the vector store"""
    try:
        # Reinitialize vector store
        doc_manager.vector_store = doc_manager.vector_store.__class__()
        query_processor.vector_store = doc_manager.vector_store
        doc_manager.processed_documents = {}
        
        # Remove saved index files
        index_files = [f"{config.FAISS_INDEX_PATH}.index", f"{config.FAISS_INDEX_PATH}.pkl"]
        for file_path in index_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
        
        logger.info("All documents cleared from vector store")
        
        return {"status": "success", "message": "All documents cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        stats = doc_manager.get_document_stats()
        
        return {
            "status": "healthy",
            "timestamp": os.times(),
            "documents_loaded": stats['total_documents'],
            "total_chunks": stats['total_chunks'],
            "vector_store_ready": doc_manager.vector_store.index.ntotal > 0,
            "Groq_key_configured": bool(config.GROQ_API_KEY),
            "config_valid": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Background task functions
async def save_vector_store_background():
    """Background task to save vector store"""
    try:
        doc_manager.save_vector_store(config.FAISS_INDEX_PATH)
        logger.info("Vector store saved in background")
    except Exception as e:
        logger.error(f"Error saving vector store in background: {e}")

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )