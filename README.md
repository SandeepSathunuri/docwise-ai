# Advanced RAG System

A sophisticated Retrieval-Augmented Generation (RAG) system with a modern React frontend and Flask backend. This system allows users to upload documents (PDF, TXT, DOCX) and ask questions about their content using AI.

## Features

### Backend Features
- **Multi-format Document Support**: PDF, TXT, and DOCX files
- **Advanced Text Processing**: Intelligent chunking with overlap for better context
- **Vector Database**: FAISS-based similarity search with persistent storage
- **Smart RAG Pipeline**: Context-aware question answering with source attribution
- **Document Management**: Upload, delete, and track document processing
- **RESTful API**: Clean API endpoints for frontend integration
- **Confidence Scoring**: AI response confidence indicators

### Frontend Features
- **Modern React UI**: Built with Material-UI components
- **Responsive Design**: Works on desktop and mobile devices
- **Drag & Drop Upload**: Easy document uploading interface
- **Real-time Chat**: Interactive chat interface with typing indicators
- **Source Attribution**: View document sources for each AI response
- **Document Management**: Visual document library with metadata
- **Dashboard**: System overview with statistics and health monitoring
- **Document Filtering**: Filter chat responses by specific documents

## Architecture

```
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── rag_pipeline.py     # RAG processing logic
│   ├── vector_database.py  # Vector storage and retrieval
│   └── document_manager.py # Document lifecycle management
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Main application pages
│   │   ├── context/        # React context for state management
│   │   └── services/       # API communication layer
│   └── public/
└── vectorstore/           # Persistent vector database storage
```

## Prerequisites

### Backend Requirements
- Python 3.8+
- Pipenv (for dependency management)
- Ollama (for embeddings)
- Groq API key (for chat completions)

### Frontend Requirements
- Node.js 16+
- npm or yarn

### AI Services Setup

1. **Install Ollama**: Visit [ollama.ai](https://ollama.ai) and install Ollama
2. **Pull the required model**:
   ```bash
   ollama pull deepseek-r1-distill-llama-70b
   ```
3. **Get Groq API Key**: Sign up at [console.groq.com](https://console.groq.com) and get your API key

## Installation

### 1. Clone and Setup Backend

```bash
# Install Python dependencies
pipenv install

# Activate virtual environment
pipenv shell

# Create uploads directory
mkdir uploads

# Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file (optional)
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env
```

## Running the Application

### Start Backend Server
```bash
# From project root, in pipenv shell
cd backend
python app.py
```
The backend will run on `http://localhost:5000`

### Start Frontend Development Server
```bash
# In a new terminal
cd frontend
npm start
```
The frontend will run on `http://localhost:3000`

## Usage

1. **Upload Documents**: 
   - Go to the Documents page
   - Drag and drop or click to upload PDF, TXT, or DOCX files
   - Wait for processing to complete

2. **Chat with Documents**:
   - Navigate to the Chat page
   - Optionally filter by specific documents
   - Ask questions about your uploaded content
   - View sources and confidence scores for each response

3. **Monitor System**:
   - Check the Dashboard for system statistics
   - View recent documents and processing status
   - Monitor system health

## API Endpoints

### Documents
- `GET /api/documents` - List all documents
- `POST /api/documents/upload` - Upload a new document
- `DELETE /api/documents/{id}` - Delete a document

### Chat
- `POST /api/chat` - Send a chat message
- `GET /api/chat/history` - Get chat history

### System
- `GET /api/health` - Health check

## Configuration

### Environment Variables
- `GROQ_API_KEY`: Your Groq API key for chat completions
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)

### Customization Options
- **Chunk Size**: Modify `chunk_size` in `vector_database.py`
- **Model Selection**: Change models in `rag_pipeline.py`
- **UI Theme**: Customize Material-UI theme in `App.js`

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**:
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is pulled: `ollama list`

2. **CORS Issues**:
   - Backend includes CORS headers
   - Check if both servers are running on correct ports

3. **File Upload Fails**:
   - Check file size (max 16MB)
   - Ensure supported file format (PDF, TXT, DOCX)
   - Verify uploads directory exists

4. **Empty Responses**:
   - Ensure documents are properly processed
   - Check vector database initialization
   - Verify Groq API key is valid

## Development

### Adding New File Types
1. Update `ALLOWED_EXTENSIONS` in `app.py`
2. Add loader logic in `vector_database.py`
3. Update frontend file type validation

### Customizing AI Responses
- Modify prompts in `rag_pipeline.py`
- Adjust confidence calculation logic
- Add new response formatting options

## Production Deployment

### Backend
- Use a production WSGI server (Gunicorn, uWSGI)
- Set up proper environment variables
- Configure database persistence
- Add authentication if needed

### Frontend
- Build for production: `npm run build`
- Serve with nginx or similar
- Update API URLs for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.