import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import re

class VectorStore:
    def __init__(self, embedding_model_name: str):
        self.embedder = SentenceTransformer(embedding_model_name)
        self.index = None
        self.chunks = []
        self.embeddings = []
        
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean the text
        text = text.strip()
        
        # Split by paragraphs first (double newline)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Keep overlap from the end of current chunk
                if overlap > 0:
                    words = current_chunk.split()
                    overlap_text = ' '.join(words[-overlap:]) if len(words) > overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Further split very large chunks
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size * 1.5:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                temp_chunk = ""
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) > chunk_size and temp_chunk:
                        final_chunks.append(temp_chunk.strip())
                        temp_chunk = sentence
                    else:
                        temp_chunk += " " + sentence if temp_chunk else sentence
                if temp_chunk:
                    final_chunks.append(temp_chunk.strip())
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def build_index(self, text: str, chunk_size: int, overlap: int):
        """Build FAISS index from text chunks."""
        # Chunk the text
        self.chunks = self.chunk_text(text, chunk_size, overlap)
        
        if not self.chunks:
            raise ValueError("No chunks were created from the text")
        
        # Generate embeddings
        self.embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True)
        
        # Build FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings.astype('float32'))
        
    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """Search for most relevant chunks."""
        if self.index is None:
            return []
        
        # Embed the query
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)
        
        # Search in FAISS
        distances, indices = self.index.search(query_embedding.astype('float32'), min(top_k, len(self.chunks)))
        
        # Return chunks with their distances
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                results.append((self.chunks[idx], float(distance)))
        
        return results