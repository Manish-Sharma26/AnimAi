/**
 * Navbar — Top navigation bar
 * Shows logo, nav links, and user info/logout when authenticated.
 */

import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/auth");
  };

  const isActive = (path) =>
    location.pathname === path ? "navbar__link navbar__link--active" : "navbar__link";

  return (
    <nav className="navbar">
      <Link to="/" className="navbar__logo">
        🎬 <span>AnimAI</span> Studio
      </Link>

      {user ? (
        <>
          <div className="navbar__links">
            <Link to="/" className={isActive("/")}>Home</Link>
            <Link to="/gallery" className={isActive("/gallery")}>My Gallery</Link>
            <Link to="/explore" className={isActive("/explore")}>Explore</Link>
          </div>

          <div className="navbar__user">
            <span className="navbar__username">{user.username}</span>
            <div className="navbar__avatar">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <button className="btn btn--ghost btn--sm" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </>
      ) : (
        <div className="navbar__links">
          <Link to="/auth" className="btn btn--primary btn--sm">
            Sign In
          </Link>
        </div>
      )}
    </nav>
  );
}
