# # services/vector_store.py

import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer

class FAISSVectorStore:
    def __init__(self, embedding_dim=384):
        self.embedding_dim = embedding_dim
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.documents = []
        self.metadata = []
        self.doc_counter = 0
        
    def add_documents(self, chunks, metadata_list):
        """Add document chunks to FAISS index"""
        embeddings = self.model.encode(chunks)
        
        #normalize the embedding for cosine similarity 
        faiss.normalize_L2(embeddings)
        
        #adding to the index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents.extend(chunks)
        self.metadata.extend(metadata_list)
        
        print(f"Added {len(chunks)} chunks to vector store. Total: {len(self.documents)}")
        
    def search(self, query, k=5):
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return [], []
            
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Get results
        results = []
        result_metadata = []
        
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.documents):
                results.append(self.documents[idx])
                result_metadata.append(self.metadata[idx])
                
        return results, result_metadata
    
    def save_index(self, filepath="vector_store"):
        """Save FAISS index and metadata"""
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Save documents and metadata
        with open(f"{filepath}.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'embedding_dim': self.embedding_dim
            }, f)
            
    def load_index(self, filepath="vector_store"):
        """Load FAISS index and metadata"""
        if os.path.exists(f"{filepath}.index") and os.path.exists(f"{filepath}.pkl"):
            self.index = faiss.read_index(f"{filepath}.index")
            
            # Load documents and metadata
            with open(f"{filepath}.pkl", 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.metadata = data['metadata']
                self.embedding_dim = data['embedding_dim']
            
            print(f"Loaded vector store with {len(self.documents)} documents")
            return True
        return False