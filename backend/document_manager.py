import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self):
        self.documents_file = "documents.json"
        self.documents = self.load_documents()
    
    def load_documents(self) -> Dict[str, Dict[str, Any]]:
        """Load documents metadata from file"""
        try:
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            return {}
    
    def save_documents(self):
        """Save documents metadata to file"""
        try:
            with open(self.documents_file, 'w') as f:
                json.dump(self.documents, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving documents: {str(e)}")
    
    def add_document(self, file_path: str, original_filename: str) -> str:
        """Add a new document to the manager"""
        doc_id = str(uuid.uuid4())
        
        document_info = {
            'id': doc_id,
            'original_filename': original_filename,
            'file_path': file_path,
            'upload_date': datetime.now().isoformat(),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'status': 'processed'
        }
        
        self.documents[doc_id] = document_info
        self.save_documents()
        
        logger.info(f"Added document {doc_id}: {original_filename}")
        return doc_id
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Get document information by ID"""
        return self.documents.get(doc_id, {})
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents"""
        return list(self.documents.values())
    
    def delete_document(self, doc_id: str):
        """Delete a document"""
        if doc_id in self.documents:
            document_info = self.documents[doc_id]
            
            # Delete physical file
            if os.path.exists(document_info['file_path']):
                try:
                    os.remove(document_info['file_path'])
                    logger.info(f"Deleted file: {document_info['file_path']}")
                except Exception as e:
                    logger.error(f"Error deleting file: {str(e)}")
            
            # Remove from documents
            del self.documents[doc_id]
            self.save_documents()
            
            logger.info(f"Deleted document {doc_id}")
        else:
            logger.warning(f"Document {doc_id} not found")
    
    def update_document_status(self, doc_id: str, status: str):
        """Update document processing status"""
        if doc_id in self.documents:
            self.documents[doc_id]['status'] = status
            self.documents[doc_id]['last_updated'] = datetime.now().isoformat()
            self.save_documents()
    
    def update_document_metadata(self, doc_id: str, pages_count: int = None, chunks_count: int = None):
        """Update document metadata with processing results"""
        if doc_id in self.documents:
            if pages_count is not None:
                self.documents[doc_id]['pages_count'] = pages_count
            if chunks_count is not None:
                self.documents[doc_id]['chunks_count'] = chunks_count
            self.documents[doc_id]['last_updated'] = datetime.now().isoformat()
            self.save_documents()
            logger.info(f"Updated metadata for document {doc_id}: pages={pages_count}, chunks={chunks_count}")
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents by filename"""
        query_lower = query.lower()
        results = []
        
        for doc_info in self.documents.values():
            if query_lower in doc_info['original_filename'].lower():
                results.append(doc_info)
        
        return results