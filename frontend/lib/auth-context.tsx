/**
 * Auth Context - Manages authentication state and tokens
 * Provides authentication utilities to the entire app
 */

'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios, { AxiosInstance } from 'axios';

interface User {
  username: string;
  email: string;
  full_name: string;
  roles: string[];
  department?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  getAuthToken: () => string | null;
  axiosInstance: AxiosInstance;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

  // Create axios instance with auth interceptor
  const axiosInstance = axios.create({
    baseURL: BACKEND_URL,
  });

  // Add auth interceptor
  axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Add response interceptor for token refresh
  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshTok = localStorage.getItem('refresh_token');
          if (refreshTok) {
            const response = await axios.post(
              `${BACKEND_URL}/auth/refresh`,
              { refresh_token: refreshTok }
            );

            const newAccessToken = response.data.access_token;
            localStorage.setItem('access_token', newAccessToken);
            setAccessToken(newAccessToken);

            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return axiosInstance(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          setUser(null);
          setAccessToken(null);
          window.location.href = '/auth/login';
        }
      }

      return Promise.reject(error);
    }
  );

  // Initialize auth on mount
  useEffect(() => {
    const initAuth = async () => {
      console.log('🔍 Auth Context: Initializing...');
      try {
        const storedToken = localStorage.getItem('access_token');
        const storedUser = localStorage.getItem('user');
        console.log('🔍 Auth Context: Token exists?', !!storedToken);
        console.log('🔍 Auth Context: User exists?', !!storedUser);

        if (storedToken && storedUser) {
          setAccessToken(storedToken);
          setUser(JSON.parse(storedUser));
          
          // Also ensure token is in cookie for middleware
          document.cookie = `access_token=${storedToken}; path=/; max-age=3600`;
          
          console.log('✅ Auth Context: User authenticated!', JSON.parse(storedUser));
        } else {
          console.log('⚠️ Auth Context: No auth data found');
        }
      } catch (error) {
        console.error('❌ Auth initialization failed:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        document.cookie = 'access_token=; path=/; max-age=0';
      } finally {
        setIsLoading(false);
        console.log('🏁 Auth Context: Initialization complete');
      }
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${BACKEND_URL}/auth/login`, {
        username,
        password,
      });

      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens in both localStorage and cookies
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }
      localStorage.setItem('user', JSON.stringify(userData));

      // Also set in cookies for middleware
      document.cookie = `access_token=${access_token}; path=/; max-age=3600`;
      if (refresh_token) {
        document.cookie = `refresh_token=${refresh_token}; path=/; max-age=604800`;
      }

      // Update state
      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      setUser(userData);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (data: any) => {
    try {
      setIsLoading(true);
      await axios.post(`${BACKEND_URL}/auth/signup`, data);
      // Signup successful, user should login
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await axios.post(
          `${BACKEND_URL}/auth/logout`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless of API response
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      // Clear cookies
      document.cookie = 'access_token=; path=/; max-age=0';
      document.cookie = 'refresh_token=; path=/; max-age=0';
      
      setUser(null);
      setAccessToken(null);
      setRefreshToken(null);
    }
  };

  const refreshAccessToken = async () => {
    try {
      const token = localStorage.getItem('refresh_token');
      if (!token) throw new Error('No refresh token');

      const response = await axios.post(`${BACKEND_URL}/auth/refresh`, {
        refresh_token: token,
      });

      const newAccessToken = response.data.access_token;
      localStorage.setItem('access_token', newAccessToken);
      setAccessToken(newAccessToken);
    } catch (error) {
      // Refresh failed, logout user
      await logout();
      throw error;
    }
  };

  const getAuthToken = (): string | null => {
    return localStorage.getItem('access_token');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
    refreshToken: refreshAccessToken,
    getAuthToken,
    axiosInstance,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
