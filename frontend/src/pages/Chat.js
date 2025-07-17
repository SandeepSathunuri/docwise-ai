import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  IconButton,
  Card,
  CardContent,
  Chip,
  Avatar,
  Divider,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  ExpandMore as ExpandMoreIcon,
  Source as SourceIcon,
  Clear as ClearIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { chatService } from '../services/api';
import { useDocuments } from '../context/DocumentContext';
import { useChat } from '../context/ChatContext';

const ChatMessage = ({ message, isUser }) => (
  <Box
    sx={{
      display: 'flex',
      mb: 2,
      justifyContent: isUser ? 'flex-end' : 'flex-start',
    }}
  >
    <Box
      sx={{
        display: 'flex',
        maxWidth: '80%',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: 1,
      }}
    >
      <Avatar
        sx={{
          bgcolor: isUser ? 'primary.main' : 'secondary.main',
          width: 32,
          height: 32,
        }}
      >
        {isUser ? <PersonIcon /> : <BotIcon />}
      </Avatar>
      <Paper
        sx={{
          p: 2,
          bgcolor: isUser ? 'primary.light' : 'grey.100',
          color: isUser ? 'primary.contrastText' : 'text.primary',
        }}
      >
        <Typography variant="body1">{message.text}</Typography>
        {message.timestamp && (
          <Typography variant="caption" sx={{ opacity: 0.7, mt: 1, display: 'block' }}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </Typography>
        )}
      </Paper>
    </Box>
  </Box>
);

const SourcesAccordion = ({ sources, confidence }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <Box sx={{ mt: 2 }}>
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SourceIcon />
            <Typography>Sources ({sources.length})</Typography>
            {confidence !== undefined && (
              <Chip
                label={`${Math.round(confidence * 100)}% confidence`}
                size="small"
                color={confidence > 0.7 ? 'success' : confidence > 0.4 ? 'warning' : 'error'}
              />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {sources.map((source, index) => (
              <Card key={index} variant="outlined">
                <CardContent sx={{ py: 1.5 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {source.filename} - Page {source.page}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {source.preview}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

const Chat = () => {
  const { documents } = useDocuments();
  const { messages, loading, sendMessage, clearChat } = useChat();
  const [inputValue, setInputValue] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const currentInput = inputValue;
    setInputValue('');

    try {
      await sendMessage(currentInput, selectedDocuments);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Container maxWidth="lg" sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Chat with Your Documents
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Ask questions about your uploaded documents
            </Typography>
          </Box>
          {messages.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                icon={<HistoryIcon />}
                label={`${messages.length} messages`}
                variant="outlined"
                size="small"
              />
              <IconButton
                onClick={clearChat}
                color="error"
                size="small"
                title="Clear chat history"
              >
                <ClearIcon />
              </IconButton>
            </Box>
          )}
        </Box>
      </Box>

      {/* Document Filter */}
      {documents.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Filter by Documents (optional)</InputLabel>
            <Select
              multiple
              value={selectedDocuments}
              onChange={(e) => setSelectedDocuments(e.target.value)}
              input={<OutlinedInput label="Filter by Documents (optional)" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((docId) => {
                    const doc = documents.find(d => d.id === docId);
                    return (
                      <Chip
                        key={docId}
                        label={doc?.original_filename || docId}
                        size="small"
                      />
                    );
                  })}
                </Box>
              )}
            >
              {documents.map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>
                  {doc.original_filename}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      )}

      {/* Chat Messages */}
      <Paper
        sx={{
          flexGrow: 1,
          p: 2,
          mb: 2,
          overflow: 'auto',
          bgcolor: 'background.default',
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <BotIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Start a conversation
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask me anything about your uploaded documents
            </Typography>
          </Box>
        ) : (
          <>
            {messages.map((message, index) => (
              <Box key={index}>
                <ChatMessage message={message} isUser={message.isUser} />
                {!message.isUser && message.sources && (
                  <SourcesAccordion sources={message.sources} confidence={message.confidence} />
                )}
                {message.isError && (
                  <Alert severity="error" sx={{ mt: 1, mb: 2 }}>
                    There was an error processing your request. Please try again.
                  </Alert>
                )}
              </Box>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                  <BotIcon />
                </Avatar>
                <Paper sx={{ p: 2, flexGrow: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Thinking...
                  </Typography>
                  <LinearProgress sx={{ mt: 1 }} />
                </Paper>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </Paper>

      {/* Input Area */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask a question about your documents..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading || documents.length === 0}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || loading || documents.length === 0}
            sx={{ alignSelf: 'flex-end' }}
          >
            <SendIcon />
          </IconButton>
        </Box>
        {documents.length === 0 && (
          <Alert severity="info" sx={{ mt: 1 }}>
            Please upload some documents first to start chatting.
          </Alert>
        )}
      </Paper>
    </Container>
  );
};

export default Chat;