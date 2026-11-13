import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { useToast } from "./ToastContext";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const { notify } = useToast();
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(true);

  // Au chargement : le cookie httpOnly est-il encore valide ?
  useEffect(() => {
    api
      .get("/users/me", { skipAuthRedirect: true })
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setBooting(false));
  }, []);

  // Intercepteur 401 -> déconnexion propre
  useEffect(() => {
    const onExpired = () => {
      setUser((u) => {
        if (u) notify("Your session expired, please log in again.", "error");
        return null;
      });
    };
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, [notify]);

  const login = useCallback(async (username, password) => {
    // Le backend attend du x-www-form-urlencoded (OAuth2PasswordRequestForm)
    await api.post("/login", new URLSearchParams({ username, password }), { skipAuthRedirect: true });
    const me = await api.get("/users/me", { skipAuthRedirect: true });
    setUser(me.data);
  }, []);

  const register = useCallback(
    async (username, email, password) => {
      await api.post("/register", { username, email, password }, { skipAuthRedirect: true });
      await login(username, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/logout", null, { skipAuthRedirect: true });
    } catch (err) {
      notify(errorMessage(err), "error");
    }
    setUser(null);
  }, [notify]);

  return <AuthContext.Provider value={{ user, booting, login, register, logout }}>{children}</AuthContext.Provider>;
}
