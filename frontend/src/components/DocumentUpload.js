import React, { useState } from 'react';
import api from '../api';
import { Box, Button, Typography, Paper, Alert, LinearProgress, IconButton } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CloseIcon from '@mui/icons-material/Close';

function DocumentUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('Select a file');
  const [uploadError, setUploadError] = useState(null);
  const [uploadedDocument, setUploadedDocument] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus(`Selected file: ${file.name}`);
      setUploadError(null);
      setUploadedDocument(null);
    } else {
      setSelectedFile(null);
      setUploadStatus('Select a file');
      setUploadError(null);
      setUploadedDocument(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Please select a file first.');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading...');
    setUploadError(null);
    setUploadedDocument(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await api.post('/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadStatus('Upload successful!');
      setUploadedDocument(response.data);
      setSelectedFile(null);
    } catch (error) {
      setUploadStatus('Upload failed.');
      if (error.response && error.response.data && error.response.data.detail) {
        setUploadError(`Upload failed: ${error.response.data.detail}`);
      } else {
        setUploadError('Upload failed. Please try again.');
      }
      setUploadedDocument(null);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Paper elevation={0} sx={{ p: 0, borderRadius: 2, background: '#f7f8fa' }}>
      <Box display="flex" alignItems="center" justifyContent="center" width="100%" gap={1}>
        <Button
          variant="outlined"
          component="label"
          color="primary"
          size="small"
          sx={{ minWidth: 0, px: 1, borderRadius: 2 }}
        >
          <CloudUploadIcon sx={{ fontSize: 36, mr: 0.5 }} />
          <input
            type="file"
            hidden
            onChange={handleFileChange}
            disabled={isUploading}
          />
        </Button>
        <Typography variant="body2" sx={{ mr: 1, minWidth: 80, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {selectedFile ? selectedFile.name : 'No file selected'}
        </Typography>
        {selectedFile && (
          <IconButton size="small" onClick={() => setSelectedFile(null)}>
            <CloseIcon fontSize="small" />
          </IconButton>
        )}
        <Button
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          size="small"
          sx={{ borderRadius: 2, minWidth: 0, px: 2 }}
        >
          {isUploading ? 'Uploading...' : 'Upload'}
        </Button>
        {isUploading && <LinearProgress sx={{ width: 80, ml: 2 }} />}
        {uploadError && <Alert severity="error" sx={{ ml: 2, p: 0.5, fontSize: 12 }}>{uploadError}</Alert>}
        {uploadedDocument && (
          <Alert severity="success" sx={{ ml: 2, p: 0.5, fontSize: 12 }}>
            Uploaded: {uploadedDocument.filename}
          </Alert>
        )}
      </Box>
    </Paper>
  );
}

export default DocumentUpload; 