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
        print(f"Loading documents from {self.knowledge_base_path}")
        loader = DirectoryLoader(
            self.knowledge_base_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        documents = loader.load()
        print(f"Loaded {len(documents)} documents")

        for i, doc in enumerate(documents):
            print(f"Document {i + 1} content preview: {doc.page_content[:100]}...")

        return documents

    def split_documents(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
        )
        splits = text_splitter.split_documents(documents)
        print(f"Created {len(splits)} splits from documents")

        for i in range(min(5, len(splits))):
            print(f"Split {i + 1} preview: {splits[i].page_content[:100]}...")

        return splits

    def create_vector_store(self, splits):
        print("Creating vector store...")
        vector_store = FAISS.from_documents(splits, self.embeddings)
        os.makedirs(self.vector_store_path, exist_ok=True)
        vector_store.save_local(self.vector_store_path)
        print(f"Vector store saved to {self.vector_store_path}")
        return vector_store

    def load_vector_store(self):
        index_path = os.path.join(self.vector_store_path, "index.faiss")

        if os.path.exists(index_path):
            print(f"Loading existing FAISS vector store from {self.vector_store_path}...")
            try:
                return FAISS.load_local(self.vector_store_path, self.embeddings,
                                        allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Error loading vector store: {e}")
                print("Will create a new vector store")
                return None
        else:
            print("Vector store not found. Creating a new one...")
            return None

    def process_and_store(self):
        documents = self.load_documents()

        if not documents:
            print("No documents found in the knowledge base!")
            return None

        splits = self.split_documents(documents)

        if not splits:
            print("No splits created from documents!")
            return None

        return self.create_vector_store(splits)

    def rebuild_vector_store(self):
        print("Rebuilding vector store from scratch...")
        documents = self.load_documents()
        splits = self.split_documents(documents)

        if not splits:
            print("No splits created for rebuilding vector store!")
            return None

        return self.create_vector_store(splits)