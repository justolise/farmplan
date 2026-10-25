import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from utils.pdf_processor import extract_text_from_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

class FarmKnowledgeBase:
    def __init__(self, api_key: str):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        self.vector_db = None
        self.db_path = "db/vector_store"

    def add_document(self, file_path: str):
        text_pages = extract_text_from_pdf(file_path)
        full_text = "\n".join(text_pages)
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.create_documents([full_text])
        
        if self.vector_db is None:
            self.vector_db = FAISS.from_documents(docs, self.embeddings)
        else:
            self.vector_db.add_documents(docs)
        
        self.vector_db.save_local(self.db_path)

    def query(self, question: str, k: int = 3):
        if self.vector_db is None:
            try:
                self.vector_db = FAISS.load_local(self.db_path, self.embeddings, allow_dangerous_deserialization=True)
            except:
                return "No knowledge base documents uploaded yet."
        
        docs = self.vector_db.similarity_search(question, k=k)
        return "\n\n".join([doc.page_content for doc in docs])

    def clear(self):
        if os.path.exists(self.db_path):
            import shutil
            shutil.rmtree(self.db_path)
        self.vector_db = None
