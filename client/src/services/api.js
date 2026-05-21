/**
 * API Service — Axios instance with auth interceptor
 * 
 * Every request to the backend goes through this instance.
 * The interceptor automatically attaches the JWT token from localStorage.
 * If the token is expired/invalid, it catches 401 and logs out.
 */

import axios from "axios";

const api = axios.create({
  baseURL: "/api",  // Vite proxy will forward to localhost:3001
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 (expired/invalid token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      // Don't redirect if already on auth page
      if (window.location.pathname !== "/auth") {
        window.location.href = "/auth";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
