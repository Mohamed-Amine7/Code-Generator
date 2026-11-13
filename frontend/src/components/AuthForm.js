import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { errorMessage } from "../api";
import BrandLogo from "./BrandLogo";

export default function AuthForm() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!isLogin) {
      if (password !== confirm)
        return setError("Les mots de passe ne correspondent pas.");
      if (
        password.length < 8 ||
        !/[A-Za-z]/.test(password) ||
        !/\d/.test(password)
      )
        return setError(
          "Le mot de passe doit contenir au moins 8 caractères, une lettre et un chiffre."
        );
    }
    setLoading(true);
    try {
      if (isLogin) await login(username, password);
      else await register(username, email, password);
    } catch (err) {
      setError(
        errorMessage(err, isLogin ? "Échec de connexion" : "Échec d'inscription")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-ledger-wrap">
      <div className="auth-ledger-card">
        {/* Brand */}
        <div className="auth-brand-top">
          <BrandLogo size={32} subtitle />
        </div>

        {/* Section stamp */}
        <div className="auth-stamp-top">
          SECTION 00 — {isLogin ? "ACCÈS ATELIER" : "CRÉER UN COMPTE"}
        </div>

        <h2 className="auth-ledger-title">
          {isLogin ? "Connexion" : "Nouvel opérateur"}
        </h2>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <form onSubmit={submit} noValidate>
          <div className="auth-field">
            <label htmlFor="auth-username">Identifiant</label>
            <input
              id="auth-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="votre_identifiant"
              required
              disabled={loading}
              autoComplete="username"
              autoFocus
            />
          </div>

          {!isLogin && (
            <div className="auth-field">
              <label htmlFor="auth-email">E-mail</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@exemple.com"
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="auth-password">Mot de passe</label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              disabled={loading}
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
          </div>

          {!isLogin && (
            <div className="auth-field">
              <label htmlFor="auth-confirm">Confirmer le mot de passe</label>
              <input
                id="auth-confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
                autoComplete="new-password"
              />
            </div>
          )}

          <button
            type="submit"
            className="btn-forge"
            disabled={loading}
            style={{ width: "100%", marginTop: "1.5rem" }}
          >
            {loading ? (
              <>
                <span className="spinner" />
                {isLogin ? "Connexion…" : "Création du compte…"}
              </>
            ) : isLogin ? (
              "⚡ Entrer dans l'atelier"
            ) : (
              "⚡ Créer mon compte"
            )}
          </button>
        </form>

        <div className="auth-switch">
          {isLogin ? "Pas encore de compte ?" : "Déjà opérateur ?"}{" "}
          <button
            type="button"
            className="auth-switch-btn"
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
            }}
          >
            {isLogin ? "Créer un compte" : "Se connecter"}
          </button>
        </div>
      </div>
    </div>
  );
}
