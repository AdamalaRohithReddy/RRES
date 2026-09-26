import React, { createContext, useContext, useState, useEffect } from 'react';
import { AuthState } from '../types';
import { api } from '../api/client';

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [auth, setAuth] = useState<AuthState>({
    token: localStorage.getItem('auth_token'),
    citizen_id: localStorage.getItem('auth_citizen_id'),
    username: localStorage.getItem('auth_username'),
    name: localStorage.getItem('auth_name'),
    role: localStorage.getItem('auth_role'),
    isAuthenticated: !!localStorage.getItem('auth_token'),
  });

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const me = await api.getMe();
          setAuth({
            token,
            citizen_id: me.citizen_id,
            username: me.username,
            name: me.name,
            role: me.role,
            isAuthenticated: true,
          });
        } catch {
          logout();
        }
      }
      setIsLoading(false);
    }
    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    const data = await api.login(username, password);
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('auth_citizen_id', data.citizen_id);
    localStorage.setItem('auth_username', data.username);
    localStorage.setItem('auth_name', data.name);
    localStorage.setItem('auth_role', data.role);

    setAuth({
      token: data.token,
      citizen_id: data.citizen_id,
      username: data.username,
      name: data.name,
      role: data.role,
      isAuthenticated: true,
    });
  };

  const register = async (userData: any) => {
    const data = await api.register(userData);
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('auth_citizen_id', data.citizen_id);
    localStorage.setItem('auth_username', data.username);
    localStorage.setItem('auth_name', data.name);
    localStorage.setItem('auth_role', data.role);

    setAuth({
      token: data.token,
      citizen_id: data.citizen_id,
      username: data.username,
      name: data.name,
      role: data.role,
      isAuthenticated: true,
    });
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_citizen_id');
    localStorage.removeItem('auth_username');
    localStorage.removeItem('auth_name');
    localStorage.removeItem('auth_role');

    setAuth({
      token: null,
      citizen_id: null,
      username: null,
      name: null,
      role: null,
      isAuthenticated: false,
    });
  };

  return (
    <AuthContext.Provider value={{ ...auth, login, register, logout, isLoading }}>
      {children}
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
