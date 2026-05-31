/**
 * useSocket — Socket.io connection hook
 * 
 * Connects DIRECTLY to the Express server (port 3001) to avoid
 * Vite's WebSocket proxy issues (ECONNABORTED on Windows).
 * Auto-reconnects and cleans up on unmount.
 */

import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import { useAuth } from "../context/AuthContext";

export default function useSocket() {
  const { token } = useAuth();
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!token) return;

    // Connect directly to the Express server — bypasses Vite's broken WS proxy
    const socket = io("http://localhost:3001", {
      auth: { token },
      transports: ["polling", "websocket"],
    });

    socket.on("connect", () => {
      console.log("[Socket] Connected to server");
      setConnected(true);
    });
    socket.on("disconnect", () => {
      console.log("[Socket] Disconnected");
      setConnected(false);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
      setConnected(false);
    };
  }, [token]);

  return { socket: socketRef.current, connected };
}
