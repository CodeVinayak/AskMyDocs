import React, { useState, useEffect } from 'react';
import axios from 'axios';

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

  if (loading) {
    return <p>Loading documents...</p>;
  }

  if (error) {
    return <p style={{ color: 'red' }}>{error}</p>;
  }

  return (
    <div>
      <h3>My Documents</h3>
      {documents.length === 0 ? (
        <p>No documents uploaded yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Upload Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map(doc => (
              <tr key={doc.id}>
                <td>{doc.filename}</td>
                <td>{new Date(doc.upload_timestamp).toLocaleDateString()}</td>
                <td>{doc.status}</td>
                <td>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deleteStatus[doc.id] === 'deleting'}
                  >
                    {deleteStatus[doc.id] === 'deleting' ? 'Deleting...' : 'Delete'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default DocumentList; 