import React from 'react';
import { useAuth } from '../context/AuthContext';
import DocumentUpload from './DocumentUpload';
import DocumentQuery from './DocumentQuery';
import DocumentList from './DocumentList';
import { Box, Button, Typography, Container, Paper, Divider } from '@mui/material';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';

function Home() {
  const { logout } = useAuth();

  return (
    <>
      <AppBar position="static" color="default" elevation={2} sx={{ mb: 4, background: 'linear-gradient(90deg, #f7f8fa 60%, #e3e8f0 100%)' }}>
        <Toolbar sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'flex-start', sm: 'center' }, py: { xs: 1, sm: 2 } }}>
          <Box display="flex" alignItems="center" flexGrow={1} mb={{ xs: 1, sm: 0 }}>
            <InsertDriveFileIcon color="primary" sx={{ fontSize: 36, mr: 2 }} />
            <Box>
              <Typography variant="h5" fontWeight={700} sx={{ color: '#22223B', lineHeight: 1 }}>
                Welcome to AskMyDocs
              </Typography>
              <Typography variant="subtitle2" color="text.secondary" sx={{ fontSize: 15, fontWeight: 400, lineHeight: 1.2 }}>
                Effortlessly upload, search, and query your documents using advanced AI.
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            color="error"
            onClick={logout}
            sx={{ fontWeight: 600, borderRadius: 2 }}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 2 }}>
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
    </>
  );
}

export default Home; 