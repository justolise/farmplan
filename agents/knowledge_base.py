import os
import re
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.pdf_processor import extract_text_from_pdf


class FarmKnowledgeBase:
    def __init__(self, api_key: str):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        self.vector_db = None
        self.db_path = "db/vector_store"
        self.raw_documents = [] # Keep track of raw chunks for keyword search

    def add_document(self, file_path: str):
        text_pages = extract_text_from_pdf(file_path)
        full_text = "\n".join(text_pages)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.create_documents([full_text])
        self.raw_documents.extend([doc.page_content for doc in docs])

        if self.vector_db is None:
            self.vector_db = FAISS.from_documents(docs, self.embeddings)
        else:
            self.vector_db.add_documents(docs)

        self.vector_db.save_local(self.db_path)

    def _keyword_search(self, query: str, k: int = 3) -> List[str]:
        """Basic BM25-like keyword matching for exact technical terms."""
        keywords = query.lower().split()
        scores = []
        for doc in self.raw_documents:
            score = sum(1 for kw in keywords if kw in doc.lower())
            if score > 0:
                scores.append((score, doc))

        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scores[:k]]

    def query(self, question: str, k: int = 3):
        if self.vector_db is None:
            try:
                self.vector_db = FAISS.load_local(self.db_path, self.embeddings, allow_dangerous_deserialization=True)
                # Note: In a production system, raw_documents should be persisted
                # alongside the FAISS index to allow keyword search after reload.
            except:  # noqa: E722
                return "No knowledge base documents uploaded yet."

        # 1. Semantic Search (Vector)
        semantic_docs = self.vector_db.similarity_search(question, k=k)
        semantic_results = [doc.page_content for doc in semantic_docs]

        # 2. Keyword Search (Exact Match)
        keyword_results = self._keyword_search(question, k=k)

        # Hybrid Merge: Combine and remove duplicates while preserving order
        combined = []
        seen = set()
        for res in semantic_results + keyword_results:
            if res not in seen:
                combined.append(res)
                seen.add(res)

        return "\n\n".join(combined[:k*2]) # Return up to 2k for better context

    def clear(self):
        if os.path.exists(self.db_path):
            import shutil
            shutil.rmtree(self.db_path)
        self.vector_db = None
        self.raw_documents = []
