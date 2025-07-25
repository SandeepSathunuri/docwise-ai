from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from rag_pipeline import RAGPipeline
from advanced_rag_pipeline import AdvancedRAGPipeline
from vector_database import VectorDatabase
from document_manager import DocumentManager
from analytics import analytics

from dotenv import load_dotenv
load_dotenv()


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
advanced_rag = AdvancedRAGPipeline(vector_db)
executor = ThreadPoolExecutor(max_workers=4)

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

@app.route('/api/chat/advanced', methods=['POST'])
def advanced_chat():
    """Advanced chat with conversation memory and enhanced features"""
    try:
        start_time = time.time()
        data = request.get_json()
        query = data.get('query', '').strip()
        document_ids = data.get('document_ids', [])
        session_id = data.get('session_id', str(uuid.uuid4()))
        model = data.get('model', 'llama-3.1-8b-instant')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Switch model if requested
        if model != advanced_rag.current_model:
            advanced_rag.switch_model(model)
        
        # Get response from advanced RAG pipeline
        response = advanced_rag.conversational_query(query, document_ids, session_id)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log analytics
        analytics.log_query(
            query=query,
            response_time=response_time,
            model_used=response.get('model_used', model),
            confidence=response.get('confidence', 0.0),
            documents_used=response.get('documents_used', 0),
            session_id=session_id,
            success='error' not in response
        )
        
        analytics.update_session(session_id, 1, response_time)
        
        # Add response time to response
        response['response_time'] = round(response_time, 3)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get available AI models"""
    try:
        models = advanced_rag.get_available_models()
        return jsonify({
            'models': models,
            'current_model': advanced_rag.current_model
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    """Switch AI model"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'error': 'Model name is required'}), 400
        
        success = advanced_rag.switch_model(model_name)
        
        if success:
            return jsonify({
                'message': f'Switched to model: {model_name}',
                'current_model': advanced_rag.current_model
            })
        else:
            return jsonify({'error': 'Invalid model name'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<doc_id>/analyze', methods=['POST'])
def analyze_document():
    """Analyze a document with AI"""
    try:
        doc_id = request.view_args['doc_id']
        doc_info = doc_manager.get_document(doc_id)
        
        if not doc_info:
            return jsonify({'error': 'Document not found'}), 404
        
        # Get document content from vector database
        vector_info = vector_db.get_document_info(doc_id)
        if not vector_info:
            return jsonify({'error': 'Document not processed yet'}), 400
        
        # Read document content
        file_path = doc_info['file_path']
        if not os.path.exists(file_path):
            return jsonify({'error': 'Document file not found'}), 404
        
        # Load and analyze document
        documents = vector_db.load_document(file_path)
        content = "\n".join([doc.page_content for doc in documents])
        
        # Run async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analysis_result = loop.run_until_complete(
            advanced_rag.analyze_document_async(content)
        )
        loop.close()
        
        # Log document analysis
        analytics.log_document_action(
            document_id=doc_id,
            document_name=doc_info['original_filename'],
            action='analyze',
            session_id=request.headers.get('X-Session-ID', 'anonymous')
        )
        
        return jsonify({
            'document_id': doc_id,
            'filename': doc_info['original_filename'],
            'analysis': analysis_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/advanced', methods=['POST'])
def advanced_search():
    """Advanced search with filters and ranking"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        filters = data.get('filters', {})
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Perform advanced search
        documents = advanced_rag.advanced_search(query, filters, limit)
        
        # Format results
        results = []
        for doc in documents:
            result = {
                'content': doc.page_content,
                'metadata': doc.metadata,
                'preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            }
            results.append(result)
        
        return jsonify({
            'query': query,
            'filters': filters,
            'results': results,
            'total_found': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get system analytics"""
    try:
        days = request.args.get('days', 7, type=int)
        report_type = request.args.get('type', 'comprehensive')
        
        if report_type == 'queries':
            data = analytics.get_query_analytics(days)
        elif report_type == 'documents':
            data = analytics.get_document_analytics(days)
        elif report_type == 'sessions':
            data = analytics.get_session_analytics(days)
        elif report_type == 'performance':
            data = analytics.get_system_performance(days)
        else:
            data = analytics.get_comprehensive_report(days)
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stats', methods=['GET'])
def get_system_stats():
    """Get real-time system statistics"""
    try:
        stats = advanced_rag.get_system_stats()
        
        # Add vector database stats
        vector_stats = {
            'total_documents': len(vector_db.document_metadata),
            'vector_store_initialized': vector_db.vector_store is not None
        }
        
        # Add document manager stats
        doc_stats = {
            'total_managed_documents': len(doc_manager.documents)
        }
        
        return jsonify({
            'rag_system': stats,
            'vector_database': vector_stats,
            'document_manager': doc_stats,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/<session_id>/summary', methods=['GET'])
def get_conversation_summary():
    """Get conversation summary for a session"""
    try:
        session_id = request.view_args['session_id']
        summary = advanced_rag.get_conversation_summary(session_id)
        
        return jsonify({
            'session_id': session_id,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/<session_id>/clear', methods=['DELETE'])
def clear_conversation():
    """Clear conversation memory for a session"""
    try:
        session_id = request.view_args['session_id']
        advanced_rag.clear_memory(session_id)
        
        return jsonify({
            'message': f'Conversation memory cleared for session: {session_id}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)