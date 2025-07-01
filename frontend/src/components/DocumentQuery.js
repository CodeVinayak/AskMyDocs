import React, { useState } from 'react';
import api from '../api';
import { Box, Button, TextField, Typography, Paper, Alert, CircularProgress } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

function DocumentQuery() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  const handleQuerySubmit = async (event) => {
    event.preventDefault();
    if (!query.trim()) {
      setError('Please enter a query.');
      setAnswer(null);
      return;
    }
    setLoading(true);
    setAnswer(null);
    setError(null);
    try {
      const response = await api.post('/query/', { query });
      setAnswer(response.data.answer);
    } catch (err) {
      setAnswer(null);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(`Query failed: ${err.response.data.detail}`);
      } else {
        setError('Query failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }}>
      <Box display="flex" flexDirection="column" alignItems="center">
        <SearchIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
        <Typography variant="h6" sx={{ mb: 2 }}>
          Ask a Question
        </Typography>
        <Box component="form" onSubmit={handleQuerySubmit} sx={{ width: '100%' }}>
          <TextField
            id="query"
            label="Your Question"
            multiline
            rows={3}
            fullWidth
            value={query}
            onChange={handleQueryChange}
            disabled={loading}
            required
            sx={{ mb: 2 }}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            startIcon={<SearchIcon />}
            disabled={loading}
          >
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Ask'}
          </Button>
        </Box>
        {error && <Alert severity="error" sx={{ width: '100%', mt: 2 }}>{error}</Alert>}
        {answer && (
          <Alert severity="success" sx={{ width: '100%', mt: 2 }}>
            <Typography variant="subtitle2">Answer:</Typography>
            <Typography variant="body2">{answer}</Typography>
          </Alert>
        )}
      </Box>
    </Paper>
  );
}

export default DocumentQuery; 