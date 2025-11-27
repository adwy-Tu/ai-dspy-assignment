import os
import glob
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Retrieval:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = docs_dir
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self._load_and_chunk_docs()
        self._build_index()

    def _load_and_chunk_docs(self):
        """Loads documents and chunks them by paragraph."""
        md_files = glob.glob(os.path.join(self.docs_dir, "*.md"))
        
        for file_path in md_files:
            filename = os.path.basename(file_path).replace(".md", "")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple paragraph splitting by double newline
            paragraphs = content.split("\n\n")
            
            for i, para in enumerate(paragraphs):
                if para.strip():
                    chunk_id = f"{filename}::chunk{i}"
                    self.chunks.append({
                        "id": chunk_id,
                        "content": para.strip(),
                        "source": filename
                    })

    def _build_index(self):
        """Builds TF-IDF index."""
        if not self.chunks:
            return
        
        corpus = [chunk["content"] for chunk in self.chunks]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k relevant chunks."""
        if not self.chunks or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0: # Only return relevant results
                result = self.chunks[idx].copy()
                result["score"] = float(similarities[idx])
                results.append(result)
        
        return results
