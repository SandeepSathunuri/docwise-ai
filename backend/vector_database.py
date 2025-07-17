from langchain_community.document_loaders import PDFPlumberLoader, TextLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import os
import uuid
from typing import List, Dict, Any
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        self.embeddings_model = self.setup_embeddings()
        self.vector_store = None
        self.document_metadata = {}  # Store document metadata
        self.db_path = "vectorstore/enhanced_db_faiss"
        self.metadata_path = "vectorstore/metadata.pkl"
        
        # Ensure directories exist
        os.makedirs("vectorstore", exist_ok=True)
        
        # Load existing vector store if available
        self.load_vector_store()
    
    def setup_embeddings(self):
        """Initialize embeddings model"""
        try:
            embeddings = OllamaEmbeddings(
                model="nomic-embed-text:latest",
                base_url="http://localhost:11434"
            )
            logger.info("Embeddings model initialized successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load document based on file type"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                loader = PDFPlumberLoader(file_path)
            elif file_extension == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_extension in ['.docx', '.doc']:
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {file_path}")
            return documents
        
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def create_chunks(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        """Split documents into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        
        # Add chunk IDs to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = str(uuid.uuid4())
            chunk.metadata['chunk_index'] = i
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def process_document(self, file_path: str, document_id: str) -> List[Document]:
        """Process a document: load, chunk, and add to vector store"""
        try:
            # Load document
            documents = self.load_document(file_path)
            
            # Add document metadata
            for doc in documents:
                doc.metadata['document_id'] = document_id
                doc.metadata['source'] = os.path.basename(file_path)
                doc.metadata['file_path'] = file_path
            
            # Create chunks
            chunks = self.create_chunks(documents)
            
            # Add to vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings_model)
            else:
                self.vector_store.add_documents(chunks)
            
            # Save vector store and metadata
            self.save_vector_store()
            
            # Store document metadata
            self.document_metadata[document_id] = {
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'chunks_count': len(chunks),
                'pages_count': len(documents)
            }
            self.save_metadata()
            
            logger.info(f"Successfully processed document {document_id}")
            return chunks
        
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents"""
        if self.vector_store is None:
            logger.warning("Vector store not initialized - no documents available")
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Found {len(docs)} similar documents for query")
            return docs
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    def similarity_search_with_filter(self, query: str, document_ids: List[str], k: int = 5) -> List[Document]:
        """Search for similar documents filtered by document IDs"""
        if self.vector_store is None:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            # Create filter for document IDs
            filter_dict = {"document_id": {"$in": document_ids}}
            docs = self.vector_store.similarity_search(query, k=k, filter=filter_dict)
            return docs
        except Exception as e:
            logger.error(f"Error in filtered similarity search: {str(e)}")
            # Fallback to regular search and manual filtering
            all_docs = self.similarity_search(query, k=k*2)
            filtered_docs = [doc for doc in all_docs if doc.metadata.get('document_id') in document_ids]
            return filtered_docs[:k]
    
    def delete_document_embeddings(self, document_id: str):
        """Delete embeddings for a specific document"""
        try:
            if self.vector_store is None:
                return
            
            # This is a limitation of FAISS - it doesn't support deletion by filter
            # In a production system, you'd use a different vector store like Pinecone or Weaviate
            # For now, we'll rebuild the vector store without the deleted document
            
            # Get all documents except the one to delete
            all_docs = []
            if hasattr(self.vector_store, 'docstore'):
                for doc_id, doc in self.vector_store.docstore._dict.items():
                    if doc.metadata.get('document_id') != document_id:
                        all_docs.append(doc)
            
            # Rebuild vector store
            if all_docs:
                self.vector_store = FAISS.from_documents(all_docs, self.embeddings_model)
            else:
                self.vector_store = None
            
            # Remove from metadata
            if document_id in self.document_metadata:
                del self.document_metadata[document_id]
            
            self.save_vector_store()
            self.save_metadata()
            
            logger.info(f"Deleted embeddings for document {document_id}")
        
        except Exception as e:
            logger.error(f"Error deleting document embeddings: {str(e)}")
            raise
    
    def save_vector_store(self):
        """Save vector store to disk"""
        try:
            if self.vector_store is not None:
                self.vector_store.save_local(self.db_path)
                logger.info("Vector store saved successfully")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
    
    def load_vector_store(self):
        """Load vector store from disk"""
        try:
            if os.path.exists(self.db_path):
                self.vector_store = FAISS.load_local(
                    self.db_path, 
                    self.embeddings_model,
                    allow_dangerous_deserialization=True
                )
                logger.info("Vector store loaded successfully")
            
            # Load metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'rb') as f:
                    self.document_metadata = pickle.load(f)
                logger.info("Document metadata loaded successfully")
        
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            self.vector_store = None
            self.document_metadata = {}
    
    def save_metadata(self):
        """Save document metadata to disk"""
        try:
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.document_metadata, f)
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
    
    def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """Get information about a specific document"""
        return self.document_metadata.get(document_id, {})
    
    def list_documents(self) -> Dict[str, Dict[str, Any]]:
        """List all documents in the vector store"""
        return self.document_metadata