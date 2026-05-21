/**
 * AuthContext — Global authentication state
 * 
 * Wraps the entire app. Provides:
 * - user: current logged-in user object (or null)
 * - token: JWT string (or null)
 * - login(email, password): authenticate and store token
 * - register(username, email, password): create account and store token
 * - logout(): clear token and redirect
 * - loading: true while checking if stored token is still valid
 * 
 * HOW IT WORKS:
 * 1. On mount, checks localStorage for a saved token
 * 2. If found, calls GET /api/auth/me to validate it
 * 3. If valid → sets user. If expired → clears token.
 * 4. All child components can use useAuth() to access auth state.
 */

import { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  // On mount: validate stored token
  useEffect(() => {
    const checkAuth = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const { data } = await api.get("/auth/me");
        setUser(data.user);
      } catch {
        // Token expired or invalid
        localStorage.removeItem("token");
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [token]);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("token", data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const register = async (username, email, password) => {
    const { data } = await api.post("/auth/register", { username, email, password });
    localStorage.setItem("token", data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
