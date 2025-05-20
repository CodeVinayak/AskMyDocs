import React from 'react';
import { useAuth } from '../context/AuthContext';
import DocumentUpload from './DocumentUpload';
import DocumentQuery from './DocumentQuery';
import DocumentList from './DocumentList';

function Home() {
  const { logout } = useAuth();

  return (
    <div>
      <h2>Welcome to AskMyDocs</h2>
      <p>This is your main application content.</p>
      {/* Add your document upload, query interface, etc. here */}

      <DocumentUpload />

      <hr />

      <DocumentQuery />

      <hr />

      <DocumentList />

      <button onClick={logout}>Logout</button>
    </div>
  );
}

export default Home; 