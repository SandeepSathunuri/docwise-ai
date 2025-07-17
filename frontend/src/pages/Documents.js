import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  Snackbar,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Description as DocumentIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useDocuments } from '../context/DocumentContext';

const FileUploadZone = ({ onFileUpload, uploading }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileUpload(acceptedFiles[0]);
      }
    },
  });

  return (
    <Card
      {...getRootProps()}
      sx={{
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.300',
        backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: 'primary.main',
          backgroundColor: 'action.hover',
        },
      }}
    >
      <input {...getInputProps()} />
      <CardContent sx={{ textAlign: 'center', py: 4 }}>
        <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          or click to select a file
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Supported formats: PDF, TXT, DOCX (Max 16MB)
        </Typography>
        {uploading && <LinearProgress sx={{ mt: 2 }} />}
      </CardContent>
    </Card>
  );
};

const DocumentCard = ({ document, onDelete, onView }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <DocumentIcon sx={{ mr: 1, mt: 0.5, color: 'primary.main' }} />
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography variant="h6" component="div" noWrap>
              {document.original_filename}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatFileSize(document.file_size)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton size="small" onClick={() => onView(document)}>
              <ViewIcon />
            </IconButton>
            <IconButton size="small" color="error" onClick={() => onDelete(document.id)}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          <Chip
            label={`${document.pages_count || 0} pages`}
            size="small"
            variant="outlined"
          />
          <Chip
            label={`${document.chunks_count || 0} chunks`}
            size="small"
            variant="outlined"
          />
          <Chip
            label={document.status}
            size="small"
            color={document.status === 'processed' ? 'success' : 'default'}
          />
        </Box>
        
        <Typography variant="caption" color="text.secondary">
          Uploaded: {new Date(document.upload_date).toLocaleDateString()}
        </Typography>
      </CardContent>
    </Card>
  );
};

const Documents = () => {
  const { documents, loading, uploadDocument, deleteDocument } = useDocuments();
  const [uploading, setUploading] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, documentId: null });
  const [viewDialog, setViewDialog] = useState({ open: false, document: null });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const handleFileUpload = async (file) => {
    try {
      setUploading(true);
      const result = await uploadDocument(file);
      setSnackbar({
        open: true,
        message: `Document "${file.name}" uploaded successfully! Created ${result.chunks_created} chunks.`,
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to upload document: ${error.message}`,
        severity: 'error',
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    try {
      await deleteDocument(deleteDialog.documentId);
      setSnackbar({
        open: true,
        message: 'Document deleted successfully!',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to delete document: ${error.message}`,
        severity: 'error',
      });
    } finally {
      setDeleteDialog({ open: false, documentId: null });
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Document Management
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Upload and manage your documents for the RAG system
        </Typography>
      </Box>

      {/* Upload Section */}
      <Box sx={{ mb: 4 }}>
        <FileUploadZone onFileUpload={handleFileUpload} uploading={uploading} />
      </Box>

      {/* Documents Grid */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" component="h2">
          Your Documents ({documents.length})
        </Typography>
      </Box>

      {loading ? (
        <LinearProgress />
      ) : documents.length === 0 ? (
        <Alert severity="info">
          No documents uploaded yet. Upload your first document using the area above.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {documents.map((document) => (
            <Grid item xs={12} sm={6} md={4} key={document.id}>
              <DocumentCard
                document={document}
                onDelete={(id) => setDeleteDialog({ open: true, documentId: id })}
                onView={(doc) => setViewDialog({ open: true, document: doc })}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, documentId: null })}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this document? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, documentId: null })}>
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Document Dialog */}
      <Dialog
        open={viewDialog.open}
        onClose={() => setViewDialog({ open: false, document: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Document Details</DialogTitle>
        <DialogContent>
          {viewDialog.document && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography><strong>Filename:</strong> {viewDialog.document.original_filename}</Typography>
              <Typography><strong>File Size:</strong> {(viewDialog.document.file_size / 1024).toFixed(2)} KB</Typography>
              <Typography><strong>Pages:</strong> {viewDialog.document.pages_count || 0}</Typography>
              <Typography><strong>Text Chunks:</strong> {viewDialog.document.chunks_count || 0}</Typography>
              <Typography><strong>Status:</strong> {viewDialog.document.status}</Typography>
              <Typography><strong>Upload Date:</strong> {new Date(viewDialog.document.upload_date).toLocaleString()}</Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialog({ open: false, document: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Documents;