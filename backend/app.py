from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import json

from rag_pipeline import RAGPipeline
from vector_database import VectorDatabase
from document_manager import DocumentManager

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
vector_db = VectorDatabase()
doc_manager = DocumentManager()
rag_pipeline = RAGPipeline(vector_db)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    try:
        documents = doc_manager.get_all_documents()
        
        # Merge metadata from vector database
        for doc in documents:
            doc_id = doc.get('id')
            if doc_id:
                vector_info = vector_db.get_document_info(doc_id)
                if vector_info:
                    doc.update({
                        'pages_count': vector_info.get('pages_count', 0),
                        'chunks_count': vector_info.get('chunks_count', 0)
                    })
                else:
                    # Set defaults if no vector info found
                    doc.setdefault('pages_count', 0)
                    doc.setdefault('chunks_count', 0)
        
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Upload and process a document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Process document
        doc_id = doc_manager.add_document(file_path, filename)
        chunks = vector_db.process_document(file_path, doc_id)
        
        # Get document info from vector database to update metadata
        vector_doc_info = vector_db.get_document_info(doc_id)
        pages_count = vector_doc_info.get('pages_count', 0)
        chunks_count = len(chunks)
        
        # Update document metadata with processing results
        doc_manager.update_document_metadata(doc_id, pages_count, chunks_count)
        
        return jsonify({
            'message': 'Document uploaded and processed successfully',
            'document_id': doc_id,
            'filename': filename,
            'pages_count': pages_count,
            'chunks_created': chunks_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document and its embeddings"""
    try:
        doc_manager.delete_document(doc_id)
        vector_db.delete_document_embeddings(doc_id)
        return jsonify({'message': 'Document deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process a chat query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        document_ids = data.get('document_ids', [])  # Optional: filter by specific documents
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get response from RAG pipeline
        response = rag_pipeline.query(query, document_ids)
        
        return jsonify({
            'response': response['answer'],
            'sources': response['sources'],
            'confidence': response.get('confidence', 0.0)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    try:
        # This would typically come from a database
        # For now, return empty array
        return jsonify({'history': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)