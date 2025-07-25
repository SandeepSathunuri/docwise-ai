import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const documentService = {
  getDocuments: () => api.get('/documents'),
  
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  deleteDocument: (documentId) => api.delete(`/documents/${documentId}`),
};

export const chatService = {
  sendMessage: (query, documentIds = []) => 
    api.post('/chat', { query, document_ids: documentIds }),
  
  sendAdvancedMessage: (query, documentIds = [], sessionId = null, model = null) =>
    api.post('/chat/advanced', { 
      query, 
      document_ids: documentIds, 
      session_id: sessionId,
      model: model 
    }),
  
  getChatHistory: () => api.get('/chat/history'),
  
  getConversationSummary: (sessionId) => api.get(`/conversation/${sessionId}/summary`),
  
  clearConversation: (sessionId) => api.delete(`/conversation/${sessionId}/clear`),
};

export const modelService = {
  getAvailableModels: () => api.get('/models'),
  
  switchModel: (modelName) => api.post('/models/switch', { model_name: modelName }),
};

export const searchService = {
  advancedSearch: (query, filters = {}, limit = 10) =>
    api.post('/search/advanced', { query, filters, limit }),
};

export const analyticsService = {
  getAnalytics: (timeRange = '7d') => api.get(`/analytics?range=${timeRange}`),
  getDocumentAnalytics: () => api.get('/analytics/documents'),
  getChatAnalytics: () => api.get('/analytics/chat'),
  getUsageStats: () => api.get('/analytics/usage'),
  getSystemStats: () => api.get('/system/stats'),
};

export const documentAnalysisService = {
  analyzeDocument: (documentId) => api.post(`/documents/${documentId}/analyze`),
};

export const healthService = {
  checkHealth: () => api.get('/health'),
};

export default api;