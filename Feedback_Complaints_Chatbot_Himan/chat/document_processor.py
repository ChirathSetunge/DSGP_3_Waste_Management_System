import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class DocumentProcessor:
    def __init__(self, knowledge_base_path, vector_store_path):
        self.knowledge_base_path = knowledge_base_path
        self.vector_store_path = vector_store_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

    def load_documents(self):
        loader = DirectoryLoader(
            self.knowledge_base_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        return loader.load()

    def split_documents(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        return text_splitter.split_documents(documents)

    def create_vector_store(self, splits):
        vector_store = FAISS.from_documents(splits, self.embeddings)
        os.makedirs(self.vector_store_path, exist_ok=True)
        vector_store.save_local(self.vector_store_path)
        return vector_store

    def load_vector_store(self):
        index_path = os.path.join(self.vector_store_path, "index.faiss")

        if os.path.exists(index_path):
            print("Loading existing FAISS vector store...")
            return FAISS.load_local(self.vector_store_path, self.embeddings,
                                    allow_dangerous_deserialization=True)
        else:
            print("Vector store not found. Creating a new one...")
            return self.process_and_store()

    def process_and_store(self):
        documents = self.load_documents()
        splits = self.split_documents(documents)

        if not splits:
            print("No documents found in the knowledge base!")
            return None

        return self.create_vector_store(splits)
