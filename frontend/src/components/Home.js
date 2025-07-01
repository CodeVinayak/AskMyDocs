import React from 'react';
import { useAuth } from '../context/AuthContext';
import DocumentUpload from './DocumentUpload';
import DocumentQuery from './DocumentQuery';
import DocumentList from './DocumentList';
import { Box, Button, Typography, Container, Paper, Divider } from '@mui/material';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

function Home() {
  const { logout } = useAuth();

  return (
    <Container maxWidth="md" sx={{ mt: 6 }}>
      <Paper elevation={4} sx={{ p: 4, borderRadius: 3, mb: 4 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <InsertDriveFileIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
          <Typography variant="h4" component="h1" fontWeight={600}>
            Welcome to AskMyDocs
          </Typography>
        </Box>
        <Typography variant="subtitle1" color="text.secondary" mb={2}>
          Effortlessly upload, search, and query your documents using advanced AI.
        </Typography>
        <Button
          variant="outlined"
          color="secondary"
          onClick={logout}
          sx={{ position: 'absolute', top: 24, right: 32 }}
        >
          Logout
        </Button>
      </Paper>

      <Paper elevation={2} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <DocumentUpload />
      </Paper>

      <Paper elevation={2} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <DocumentQuery />
      </Paper>

      <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
        <DocumentList />
      </Paper>
    </Container>
  );
}

export default Home; 