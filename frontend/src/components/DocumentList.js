import React, { useState, useEffect } from 'react';
import api from '../api';
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
  Alert,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import DescriptionIcon from '@mui/icons-material/Description';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DownloadIcon from '@mui/icons-material/Download';
import { useTheme, useMediaQuery } from '@mui/material';

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteStatus, setDeleteStatus] = useState({}); // To track deletion status per document
  const [confirmDelete, setConfirmDelete] = useState({ open: false, doc: null });

  // Function to fetch documents from the backend
  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/documents/');
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
      await api.delete(`/documents/${documentId}`);

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

  const getFileIcon = (filename) => {
    if (filename.toLowerCase().endsWith('.pdf')) return <PictureAsPdfIcon color="error" sx={{ mr: 1 }} />;
    if (filename.toLowerCase().endsWith('.txt')) return <DescriptionIcon color="primary" sx={{ mr: 1 }} />;
    // Add more types as needed
    return <InsertDriveFileIcon color="action" sx={{ mr: 1 }} />;
  };

  const getStatusDot = (status) => {
    let color = '#22C55E'; // processed
    if (status === 'processing') color = '#F59E42';
    if (status === 'failed' || status === 'es_indexing_failed' || status === 'db_save_failed') color = '#EF4444';
    return <Box component="span" sx={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: color, mr: 1, verticalAlign: 'middle' }} />;
  };

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleDeleteClick = (doc) => setConfirmDelete({ open: true, doc });
  const handleConfirmDelete = async () => {
    if (confirmDelete.doc) await handleDelete(confirmDelete.doc.id);
    setConfirmDelete({ open: false, doc: null });
  };
  const handleCancelDelete = () => setConfirmDelete({ open: false, doc: null });

  return (
    <Paper elevation={1} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 3, background: '#f7f8fa', boxShadow: '0 4px 24px rgba(60,72,100,0.08)' }}>
      <Box display="flex" alignItems="center" mb={2}>
        <DescriptionIcon color="primary" sx={{ fontSize: 28, mr: 1 }} />
        <Typography variant="h6" fontWeight={600}>My Documents</Typography>
      </Box>
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={120}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <TableContainer sx={{ borderRadius: 2, boxShadow: '0 2px 8px rgba(59,130,246,0.06)' }}>
          <Table size={isMobile ? 'small' : 'medium'}>
            <TableHead>
              <TableRow sx={{ background: '#eaf1fb' }}>
                <TableCell sx={{ fontWeight: 700 }}>Filename</TableCell>
                {!isMobile && <TableCell sx={{ fontWeight: 700 }}>Upload Date</TableCell>}
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Box display="flex" flexDirection="column" alignItems="center" py={3}>
                      <InsertDriveFileIcon color="disabled" sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="body2" color="text.secondary">No documents uploaded yet. Start by uploading one above!</Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map(doc => (
                  <TableRow key={doc.id} sx={{ background: doc.id % 2 === 0 ? '#f7f8fa' : '#fff' }}>
                    <TableCell sx={{ fontSize: { xs: 14, sm: 16 } }}>
                      <Box display="flex" alignItems="center">
                        {getFileIcon(doc.filename)}
                        <Typography variant="body2" fontWeight={500} sx={{ fontSize: { xs: 14, sm: 16 } }}>{doc.filename}</Typography>
                      </Box>
                      {isMobile && (
                        <Box mt={1} display="flex" flexDirection="column" gap={0.5}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 12 }}>{new Date(doc.upload_timestamp).toLocaleDateString()}</Typography>
                          <Box display="flex" alignItems="center" gap={1}>
                            {getStatusDot(doc.status)}
                            <Typography variant="body2" component="span" sx={{ fontSize: 13 }}>{doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}</Typography>
                            <Tooltip title="Delete">
                              <IconButton color="error" size="small" onClick={() => handleDeleteClick(doc)} disabled={deleteStatus[doc.id] === 'deleting'}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                      )}
                    </TableCell>
                    {!isMobile && <TableCell sx={{ fontSize: 14 }}>{new Date(doc.upload_timestamp).toLocaleDateString()}</TableCell>}
                    {!isMobile && <TableCell sx={{ fontSize: 14 }}>{getStatusDot(doc.status)}<Typography variant="body2" component="span" sx={{ fontSize: 14 }}>{doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}</Typography></TableCell>}
                    {!isMobile && <TableCell>
                      <Tooltip title="Delete">
                        <IconButton color="error" onClick={() => handleDeleteClick(doc)} disabled={deleteStatus[doc.id] === 'deleting'}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      <Dialog open={confirmDelete.open} onClose={handleCancelDelete}>
        <DialogTitle>Delete Document</DialogTitle>
        <DialogContent>
          Are you sure you want to delete <b>{confirmDelete.doc?.filename}</b>?
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} color="primary">Cancel</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">Yes, Delete</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

export default DocumentList; 