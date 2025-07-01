import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import DescriptionIcon from '@mui/icons-material/Description';

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteStatus, setDeleteStatus] = useState({}); // To track deletion status per document

  // Function to fetch documents from the backend
  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/documents/`);
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      // Display the error message from the backend
      if (err.response && err.response.data && err.response.data.detail) {
          setError(`Failed to load documents: ${err.response.data.detail}`);
      } else {
          setError('Failed to load documents.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Fetch documents when the component mounts
  useEffect(() => {
    fetchDocuments();
  }, []); // Empty dependency array means this runs once on mount

  // Function to handle document deletion
  const handleDelete = async (documentId) => {
    // Set status to deleting for the specific document
    setDeleteStatus(prevStatus => ({ ...prevStatus, [documentId]: 'deleting' }));
    setError(null);

    try {
      await axios.delete(`${process.env.REACT_APP_API_URL}/documents/${documentId}`);

      // On successful deletion, remove the document from the list state
      setDocuments(prevDocuments => prevDocuments.filter(doc => doc.id !== documentId));
      setDeleteStatus(prevStatus => ({ ...prevStatus, [documentId]: 'deleted' }));

    } catch (err) {
      console.error(`Failed to delete document ${documentId}:`, err);
      // Set status to error for the specific document
      setDeleteStatus(prevStatus => ({ ...prevStatus, [documentId]: 'error' }));
      // Display the error message from the backend
      if (err.response && err.response.data && err.response.data.detail) {
           setError(`Failed to delete document: ${err.response.data.detail}`);
       } else {
           setError('Failed to delete document. Please try again.');
       }
    }
  };

  return (
    <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <DescriptionIcon color="primary" sx={{ fontSize: 28, mr: 1 }} />
        <Typography variant="h6">My Documents</Typography>
      </Box>
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={120}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Filename</TableCell>
                <TableCell>Upload Date</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    No documents uploaded yet.
                  </TableCell>
                </TableRow>
              ) : (
                documents.map(doc => (
                  <TableRow key={doc.id}>
                    <TableCell>{doc.filename}</TableCell>
                    <TableCell>{new Date(doc.upload_timestamp).toLocaleDateString()}</TableCell>
                    <TableCell>{doc.status}</TableCell>
                    <TableCell>
                      <Button
                        variant="outlined"
                        color="error"
                        size="small"
                        startIcon={<DeleteIcon />}
                        onClick={() => handleDelete(doc.id)}
                        disabled={deleteStatus[doc.id] === 'deleting'}
                      >
                        {deleteStatus[doc.id] === 'deleting' ? 'Deleting...' : 'Delete'}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
}

export default DocumentList; 