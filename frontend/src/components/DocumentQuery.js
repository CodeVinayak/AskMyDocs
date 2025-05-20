import React, { useState } from 'react';
import axios from 'axios';

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
      // Send the query to the backend /query endpoint
      // Assuming the backend expects a JSON body like { "query": "user question" }
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/query/`, { query });

      setAnswer(response.data.answer); // Assuming backend returns { "answer": "..." }

    } catch (err) {
      console.error('Query failed:', err);
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
    <div>
      <h3>Ask a Question</h3>
      <form onSubmit={handleQuerySubmit}>
        <div>
          <label htmlFor="query">Your Question:</label>
          <textarea
            id="query"
            rows="4"
            cols="50"
            value={query}
            onChange={handleQueryChange}
            disabled={loading}
            required
          ></textarea>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Ask'}
        </button>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {answer && (
        <div>
          <h4>Answer:</h4>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}

export default DocumentQuery; 