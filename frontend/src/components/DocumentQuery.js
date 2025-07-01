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
    <Paper elevation={1} sx={{ p: { xs: 2, sm: 3 }, borderRadius: 3, background: '#f7f8fa' }}>
      <Box display="flex" flexDirection="column" alignItems="center" width="100%">
        <SearchIcon color="primary" sx={{ fontSize: 36, mb: 1 }} />
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Ask a Question
        </Typography>
        <Box component="form" onSubmit={handleQuerySubmit} sx={{ width: '100%' }}>
          <TextField
            id="query"
            label="Ask a question about your documents... (e.g., 'What are the key findings?')"
            multiline
            rows={3}
            fullWidth
            value={query}
            onChange={handleQueryChange}
            disabled={loading}
            required
            sx={{ mb: 2, borderRadius: 2, background: '#fff', boxShadow: loading ? '0 0 0 2px #3B82F6' : 'none', border: '1px solid #e0e7ef' }}
            InputProps={{ style: { borderRadius: 12 } }}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            startIcon={<SearchIcon />}
            disabled={loading}
            sx={{ fontWeight: 700, borderRadius: 2 }}
          >
            Ask
          </Button>
        </Box>
        {error && <Alert severity="error" sx={{ width: '100%', mt: 2 }}>{error}</Alert>}
        {answer && (
          <Box sx={{ width: '100%', mt: 2, background: '#eaf1fb', border: '1px solid #b6d4fe', borderRadius: 2, p: 2, boxShadow: '0 2px 8px rgba(59,130,246,0.06)' }}>
            <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', color: '#22C55E', fontWeight: 600, mb: 1 }}>
              ✓ Answer
            </Typography>
            <Typography variant="body2" sx={{ lineHeight: 1.7 }}>{answer}</Typography>
          </Box>
        )}
        {loading && !answer && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            <CircularProgress size={18} sx={{ mr: 1 }} /> Thinking...
          </Typography>
        )}
      </Box>
    </Paper>
  );
}

export default DocumentQuery; 