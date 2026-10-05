import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import axios from "axios";
import type { CurrentUser } from "../types/jobs";

type AuthValue = {
  user: CurrentUser | null;
  initializing: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    axios.get<CurrentUser>("/api/auth/me")
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setInitializing(false));
  }, []);

  async function login(username: string, password: string) {
    const { data } = await axios.post<CurrentUser>("/api/auth/login", { username, password });
    setUser(data);
  }

  async function logout() {
    try { await axios.post("/api/auth/logout"); } finally { setUser(null); }
  }

  return <AuthContext.Provider value={{ user, initializing, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is missing");
  return value;
}
