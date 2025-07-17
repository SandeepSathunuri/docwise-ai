import React, { createContext, useContext, useState, useEffect } from 'react';
import { chatService } from '../services/api';

const ChatContext = createContext();

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Load messages from localStorage on component mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    const savedSessionId = localStorage.getItem('chatSessionId');
    
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (error) {
        console.error('Error loading saved messages:', error);
      }
    }
    
    if (savedSessionId) {
      setSessionId(savedSessionId);
    } else {
      // Generate new session ID
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      localStorage.setItem('chatSessionId', newSessionId);
    }
  }, []);

  // Save messages to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
    }
  }, [messages]);

  const sendMessage = async (inputValue, selectedDocuments = []) => {
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      text: inputValue,
      isUser: true,
      timestamp: new Date().toISOString(),
      sessionId,
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await chatService.sendMessage(inputValue, selectedDocuments);
      const { response: aiResponse, sources, confidence } = response.data;

      const aiMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        text: aiResponse,
        isUser: false,
        timestamp: new Date().toISOString(),
        sources,
        confidence,
        sessionId,
      };

      setMessages(prev => [...prev, aiMessage]);
      return aiMessage;
    } catch (error) {
      const errorMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        text: `Sorry, I encountered an error: ${error.message}`,
        isUser: false,
        timestamp: new Date().toISOString(),
        isError: true,
        sessionId,
      };
      setMessages(prev => [...prev, errorMessage]);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('chatMessages');
    // Generate new session ID
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    localStorage.setItem('chatSessionId', newSessionId);
  };

  const deleteMessage = (messageId) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  };

  const getMessagesBySession = (sessionId) => {
    return messages.filter(msg => msg.sessionId === sessionId);
  };

  const getAllSessions = () => {
    const sessions = {};
    messages.forEach(msg => {
      if (!sessions[msg.sessionId]) {
        sessions[msg.sessionId] = {
          id: msg.sessionId,
          messages: [],
          lastActivity: msg.timestamp,
          messageCount: 0,
        };
      }
      sessions[msg.sessionId].messages.push(msg);
      sessions[msg.sessionId].messageCount++;
      if (msg.timestamp > sessions[msg.sessionId].lastActivity) {
        sessions[msg.sessionId].lastActivity = msg.timestamp;
      }
    });
    return Object.values(sessions).sort((a, b) => new Date(b.lastActivity) - new Date(a.lastActivity));
  };

  const switchToSession = (sessionId) => {
    setSessionId(sessionId);
    localStorage.setItem('chatSessionId', sessionId);
  };

  const createNewSession = () => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    localStorage.setItem('chatSessionId', newSessionId);
    return newSessionId;
  };

  const value = {
    messages: messages.filter(msg => msg.sessionId === sessionId),
    allMessages: messages,
    loading,
    sessionId,
    sendMessage,
    clearChat,
    deleteMessage,
    getMessagesBySession,
    getAllSessions,
    switchToSession,
    createNewSession,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};