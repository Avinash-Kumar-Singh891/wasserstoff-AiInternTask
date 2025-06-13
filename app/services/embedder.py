# # services/embedder.py
# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer('all-MiniLM-L6-v2')

# def chunk_text(text, chunk_size=200):
#     sentences = text.split('. ')
#     chunks, current = [], ""
#     for sentence in sentences:
#         if len(current) + len(sentence) <= chunk_size:
#             current += sentence + ". "
#         else:
#             chunks.append(current.strip())
#             current = sentence + ". "
#     if current:
#         chunks.append(current.strip())
#     return chunks

# def embed_chunks(chunks):
#     return model.encode(chunks)
# services/embedder.py (updated for new structure)
from sentence_transformers import SentenceTransformer
import re

class DocumentEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def chunk_text(self, text, chunk_size=300, overlap=50):
        """Enhanced text chunking with overlap"""
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-overlap//10:] if len(words) > overlap//10 else []
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def process_document(self, text_chunks_with_metadata):
        """Process document chunks with metadata"""
        processed_chunks = []
        processed_metadata = []
        
        for chunk_data in text_chunks_with_metadata:
            text = chunk_data['text']
            metadata = chunk_data['metadata']
            
            # Further chunk if text is too long
            sub_chunks = self.chunk_text(text)
            
            for i, sub_chunk in enumerate(sub_chunks):
                processed_chunks.append(sub_chunk)
                # Add sub-chunk info to metadata
                sub_metadata = metadata.copy()
                sub_metadata['sub_chunk'] = i
                processed_metadata.append(sub_metadata)
        
        return processed_chunks, processed_metadata
    
    def embed_chunks(self, chunks):
        """Generate embeddings for text chunks"""
        return self.model.encode(chunks)