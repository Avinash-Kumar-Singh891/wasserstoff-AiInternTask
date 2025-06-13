# services/document_manager.py 
from .ocr import (
    extract_text_from_pdf, extract_text_from_image,
    extract_text_from_csv, extract_text_from_docx
)

from .embedder import DocumentEmbedder
from .vector_store import FAISSVectorStore
import os

class DocumentManager:
    def __init__(self):
        self.vector_store = FAISSVectorStore()
        self.embedder = DocumentEmbedder()
        self.processed_documents = {}
        
    def upload_and_process_document(self, file_path, doc_id=None):
        """Upload and process a single document"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        doc_id = doc_id or os.path.basename(file_path)

        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            text_chunks_with_metadata = extract_text_from_pdf(file_path, doc_id)
        elif file_ext in ['.jpg','.jpeg','.png','.tiff','.bmp']:
            text_chunks_with_metadata=extract_text_from_image(file_path, doc_id)
        elif file_ext == '.txt' or file_ext == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                text_chunks_with_metadata = [{
                    'text': text,
                    'metadata': {
                        'doc_id': doc_id,
                        'page': 1,
                        'paragraph': 1,
                        'source': file_path
                    }
                }]
        elif file_ext == '.csv':
            text_chunks_with_metadata = extract_text_from_csv(file_path, doc_id)
        elif file_ext == '.docx':
            text_chunks_with_metadata = extract_text_from_docx(file_path, doc_id)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        chunks, metadata_list=self.embedder.process_document(text_chunks_with_metadata)
        self.vector_store.add_documents(chunks, metadata_list)
        self.processed_documents[doc_id] = {
            'path': file_path,
            'chunks_count': len(chunks),
            'processed': True
        }
        
        return len(chunks)
    
    def batch_upload_documents(self, file_paths):
        """Upload and process multiple documents"""
        results = {}
        
        for file_path in file_paths:
            try:
                chunk_count = self.upload_and_process_document(file_path)
                results[file_path] = {'success': True, 'chunks': chunk_count}
            except Exception as e:
                results[file_path] = {'success': False, 'error': str(e)}
        
        return results
    
    def get_document_stats(self):
        """Get statistics about processed documents"""
        total_docs = len(self.processed_documents)
        total_chunks = sum(doc['chunks_count'] for doc in self.processed_documents.values())
        
        return {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'documents': self.processed_documents
        }
    
    def save_vector_store(self, filepath="vector_store"):
        """Save the vector store to disk"""
        self.vector_store.save_index(filepath)
    
    def load_vector_store(self, filepath="vector_store"):
        """Load the vector store from disk"""
        return self.vector_store.load_index(filepath)