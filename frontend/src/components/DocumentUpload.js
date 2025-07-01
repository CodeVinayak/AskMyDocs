import React, { useState } from 'react';
import axios from 'axios';
import { Box, Button, Typography, Paper, Alert, LinearProgress } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

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
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/upload/`, formData, {
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
    <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }}>
      <Box display="flex" flexDirection="column" alignItems="center">
        <CloudUploadIcon color="primary" sx={{ fontSize: 36, mb: 1 }} />
        <Typography variant="h6" sx={{ mb: 2 }}>
          Upload Document
        </Typography>
        <input
          type="file"
          onChange={handleFileChange}
          disabled={isUploading}
          style={{ marginBottom: 16 }}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          startIcon={<CloudUploadIcon />}
          sx={{ mb: 2 }}
        >
          {isUploading ? 'Uploading...' : 'Upload'}
        </Button>
        {isUploading && <LinearProgress sx={{ width: '100%', mb: 2 }} />}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {uploadStatus}
        </Typography>
        {uploadError && <Alert severity="error" sx={{ width: '100%', mb: 1 }}>{uploadError}</Alert>}
        {uploadedDocument && (
          <Alert severity="success" sx={{ width: '100%' }}>
            <Typography variant="subtitle2">Uploaded Document Info:</Typography>
            <Typography variant="body2">ID: {uploadedDocument.document_id}</Typography>
            <Typography variant="body2">Filename: {uploadedDocument.filename}</Typography>
            <Typography variant="body2">Status: {uploadedDocument.status}</Typography>
          </Alert>
        )}
      </Box>
    </Paper>
  );
}

export default DocumentUpload; 