/**
 * App — Root component with routing
 * 
 * Protected routes redirect to /auth if not logged in.
 * Auth page redirects to / if already logged in.
 */

import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import AuthPage from "./pages/Auth";
import Home from "./pages/Home";
import Studio from "./pages/Studio";
import Gallery from "./pages/Gallery";
import Explore from "./pages/Explore";

// Protected route wrapper — redirects to /auth if not logged in
function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", marginTop: "4rem" }}>
        <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
      </div>
    );
  }

  return user ? <Outlet /> : <Navigate to="/auth" replace />;
}

function AppRoutes() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Public */}
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/explore" element={<Explore />} />

        {/* Protected */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Home />} />
          <Route path="/studio/:id" element={<Studio />} />
          <Route path="/gallery" element={<Gallery />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
