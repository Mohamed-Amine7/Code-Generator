import React, { useCallback, useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import useModelStatus from "./hooks/useModelStatus";
import AuthForm from "./components/AuthForm";
import GenerateTab from "./components/GenerateTab";
import AnalyzeTab from "./components/AnalyzeTab";
import TextAnalysisTab from "./components/TextAnalysisTab";
import HistoryModal from "./components/HistoryModal";
import FeedbackSystem from "./components/FeedbackSystem";
import BrandLogo from "./components/BrandLogo";
import "./App.css";

const TABS = [
  { id: "generate", index: "01", label: "Générer" },
  { id: "analyze",  index: "02", label: "Analyser" },
  { id: "mission1", index: "03", label: "Intention" },
  { id: "mission2", index: "04", label: "Qualité" },
];

function Shell() {
  const { user, booting, logout } = useAuth();
  const [tab, setTab] = useState("generate");
  const [showHistory, setShowHistory] = useState(false);
  const [fromHistory, setFromHistory] = useState(null);
  const [darkMode, setDarkMode] = useState(true);
  const modelStatus = useModelStatus(Boolean(user));
  const consumed = useCallback(() => setFromHistory(null), []);

  // Sync dark/light theme on <html>
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        if (user) setShowHistory((v) => !v);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [user]);

  if (booting) {
    return (
      <div className="calibre-shell">
        <div className="atelier-boot">
          <span className="spinner" />
          <span className="boot-label">CALIBRE initialise…</span>
        </div>
      </div>
    );
  }

  if (!user) return <AuthForm />;

  const loadingModels = Object.entries(modelStatus.models || {})
    .filter(([, v]) => v === "pending" || v === "loading")
    .map(([k]) => k.replace("_", " "));

  return (
    <div className="calibre-shell">
      {/* ── NAV ── */}
      <nav className="atelier-nav" role="banner">
        <BrandLogo size={28} subtitle={false} />

        <div className="nav-controls">
          {!modelStatus.ready && (
            <div className="status-pill" role="status" aria-live="polite">
              <span className="status-dot warmup" />
              {loadingModels.join(", ") || "démarrage"} en cours…
            </div>
          )}

          <span className="user-tag">
            Atelier de <strong>{user.username}</strong>
          </span>

          <button
            className="btn-control"
            onClick={() => setShowHistory(true)}
            title="Ouvrir le Ledger (Ctrl+K)"
            aria-label="Historique des générations"
          >
            Ledger
          </button>

          <button
            className="btn-control"
            onClick={() => setDarkMode((v) => !v)}
            title="Basculer thème clair / sombre"
            aria-label="Changer de thème"
          >
            {darkMode ? "☀" : "☾"}
          </button>

          <button
            className="btn-control btn-control--exit"
            onClick={logout}
            aria-label="Se déconnecter"
          >
            Sortir
          </button>
        </div>
      </nav>

      {/* ── TAB BAR ── */}
      <div className="atelier-tabs" role="tablist" aria-label="Sections">
        {TABS.map(({ id, index, label }) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            className={`atelier-tab-btn${tab === id ? " active" : ""}`}
            onClick={() => setTab(id)}
          >
            <span className="tab-idx">{index}</span>
            <span className="tab-lbl">{label}</span>
          </button>
        ))}
      </div>

      {/* ── CONTENT ── */}
      <main className="atelier-main" role="main">
        {tab === "generate" && (
          <GenerateTab initial={fromHistory} onInitialConsumed={consumed} />
        )}
        {tab === "analyze"  && <AnalyzeTab />}
        {tab === "mission1" && <TextAnalysisTab />}
        {tab === "mission2" && <FeedbackSystem />}
      </main>

      {/* ── HISTORY DRAWER ── */}
      {showHistory && (
        <HistoryModal
          onClose={() => setShowHistory(false)}
          onSelect={(item) => {
            setFromHistory(item);
            setTab("generate");
            setShowHistory(false);
          }}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </ToastProvider>
  );
}
