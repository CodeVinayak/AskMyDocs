import React, { useState } from 'react';
import axios from 'axios';

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
      // Use the axios instance which is already configured with the JWT interceptor
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Optional: Track upload progress
        // onUploadProgress: (progressEvent) => {
        //   const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        //   setUploadStatus(`Uploading... ${percentCompleted}%`);
        // }
      });

      setUploadStatus('Upload successful!');
      setUploadedDocument(response.data);
      setSelectedFile(null); // Clear selected file after successful upload
      console.log('Upload response:', response.data);

    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('Upload failed.');
      // Handle specific error responses (e.g., server errors)
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
    <div>
      <h3>Upload Document</h3>
      <input type="file" onChange={handleFileChange} disabled={isUploading} />
      <button onClick={handleUpload} disabled={!selectedFile || isUploading}>
        {isUploading ? 'Uploading...' : 'Upload'}
      </button>
      <p>{uploadStatus}</p>
      {uploadError && <p style={{ color: 'red' }}>{uploadError}</p>}
      {uploadedDocument && (
        <div>
          <h4>Uploaded Document Info:</h4>
          <p>ID: {uploadedDocument.document_id}</p>
          <p>Filename: {uploadedDocument.filename}</p>
          <p>Status: {uploadedDocument.status}</p>
        </div>
      )}
    </div>
  );
}

export default DocumentUpload; 