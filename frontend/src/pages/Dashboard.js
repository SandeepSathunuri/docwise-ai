import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Description as DocumentIcon,
  Chat as ChatIcon,
  Storage as StorageIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';
import { useDocuments } from '../context/DocumentContext';
import { useChat } from '../context/ChatContext';
import { healthService } from '../services/api';

const StatCard = ({ title, value, icon, color = 'primary' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            backgroundColor: `${color}.light`,
            borderRadius: '50%',
            p: 1,
            mr: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </Box>
        <Typography variant="h6" component="div">
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" component="div" color={`${color}.main`}>
        {value}
      </Typography>
    </CardContent>
  </Card>
);

const Dashboard = () => {
  const { documents, loading } = useDocuments();
  const { getAllSessions, allMessages } = useChat();
  const [systemHealth, setSystemHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  useEffect(() => {
    const checkSystemHealth = async () => {
      try {
        await healthService.checkHealth();
        setSystemHealth('healthy');
      } catch (error) {
        setSystemHealth('unhealthy');
      } finally {
        setHealthLoading(false);
      }
    };

    checkSystemHealth();
  }, []);

  const totalDocuments = documents.length;
  const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks_count || 0), 0);
  const totalPages = documents.reduce((sum, doc) => sum + (doc.pages_count || 0), 0);
  const totalSessions = getAllSessions().length;
  const totalMessages = allMessages.length;

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Welcome to your Advanced RAG System
        </Typography>
      </Box>

      {/* System Health */}
      <Box sx={{ mb: 3 }}>
        {healthLoading ? (
          <LinearProgress />
        ) : (
          <Alert 
            severity={systemHealth === 'healthy' ? 'success' : 'error'}
            sx={{ mb: 2 }}
          >
            System Status: {systemHealth === 'healthy' ? 'All systems operational' : 'Backend connection failed'}
          </Alert>
        )}
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Documents"
            value={loading ? '...' : totalDocuments}
            icon={<DocumentIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Pages"
            value={loading ? '...' : totalPages}
            icon={<StorageIcon />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Text Chunks"
            value={loading ? '...' : totalChunks}
            icon={<TrendingIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Chat Messages"
            value={totalMessages}
            icon={<ChatIcon />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Recent Documents */}
      <Card>
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            Recent Documents
          </Typography>
          {loading ? (
            <LinearProgress />
          ) : documents.length === 0 ? (
            <Typography color="text.secondary">
              No documents uploaded yet. Go to the Documents page to upload your first document.
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {documents.slice(0, 5).map((doc) => (
                <Box
                  key={doc.id}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                  }}
                >
                  <Box>
                    <Typography variant="subtitle1">
                      {doc.original_filename}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uploaded: {new Date(doc.upload_date).toLocaleDateString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label={`${doc.pages_count || 0} pages`}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={doc.status}
                      size="small"
                      color={doc.status === 'processed' ? 'success' : 'default'}
                    />
                  </Box>
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default Dashboard;