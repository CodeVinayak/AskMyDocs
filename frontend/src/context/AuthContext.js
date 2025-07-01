import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // To check auth status on load

  // Function to get the JWT token from storage
  const getToken = () => {
    return localStorage.getItem('accessToken');
  };

  // Function to set the JWT token in storage
  const setToken = (token) => {
    localStorage.setItem('accessToken', token);
  };

  // Function to remove the JWT token from storage
  const removeToken = () => {
    localStorage.removeItem('accessToken');
  };

  // Check authentication status on component mount
  useEffect(() => {
    const token = getToken();
    if (token) {
      // In a real app, you might want to verify the token with the backend
      // or fetch user details here. For simplicity, we'll assume a token means authenticated.
      setIsAuthenticated(true);
      // TODO: Fetch user details if needed
    }
    setLoading(false); // Auth check is done
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      // Replace with your backend login endpoint
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/auth/login`, {
        email,
        password,
      });

      const { access_token } = response.data;
      setToken(access_token);
      setIsAuthenticated(true);
      // TODO: Fetch user details after login if needed
      return true; // Indicate successful login
    } catch (error) {
      console.error('Login failed:', error);
      setIsAuthenticated(false);
      removeToken();
      // Handle specific error responses (e.g., invalid credentials)
      if (error.response && error.response.status === 401) {
          throw new Error("Invalid email or password");
      } else {
          throw new Error("Login failed. Please try again.");
      }
    }
  };

  // Register function
  const register = async (username, email, password) => {
      try {
          console.log("API URL:", process.env.REACT_APP_API_URL);
          // Replace with your backend register endpoint
          const response = await axios.post(`${process.env.REACT_APP_API_URL}/auth/register`, {
              username,
              email,
              password
          });
          // Assuming successful registration returns user data or a success indicator
          console.log('Registration successful:', response.data);
          return true; // Indicate successful registration
      } catch (error) {
          console.error('Registration failed:', error);
          // Handle specific error responses (e.g., email/username already exists)
           if (error.response && error.response.status === 400) {
               throw new Error("Email or username already exists.");
           } else {
               throw new Error("Registration failed. Please try again.");
           }
      }
  };

  // Logout function
  const logout = () => {
    removeToken();
    setIsAuthenticated(false);
    setUser(null);
    // Redirect handled by ProtectedRoute or calling component
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, loading, login, register, logout, getToken }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 