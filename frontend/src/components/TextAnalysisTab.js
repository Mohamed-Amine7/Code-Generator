import React, { useState } from "react";
import { api, errorMessage } from "../api";
import { useToast } from "../context/ToastContext";

export default function TextAnalysisTab() {
  const { notify } = useToast();
  const [text, setText]     = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const analyze = async () => {
    if (!text.trim()) return notify("Écris ton texte à analyser !", "error");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post("/analyze", { text });
      setResult(data);
    } catch (err) {
      notify(errorMessage(err, "Erreur d'analyse"), "error");
    } finally {
      setLoading(false);
    }
  };

  const sorted = result
    ? Object.entries(result.scores || {}).sort((a, b) => b[1] - a[1])
    : [];

  const topScore = sorted[0]?.[1] ?? 0;

  return (
    <div className="workbench-grid">
      {/* ── LEFT ── */}
      <div className="atelier-input-card">
        <div className="panel-header-editorial">
          <span className="section-label">03 / DÉTECTION D'INTENTION</span>
        </div>

        <div className="prompt-area-wrap">
          <textarea
            className="calibre-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={9}
            maxLength={5000}
            placeholder="Décrivez votre intention ici… (FR, EN ou AR)"
            disabled={loading}
            aria-label="Texte à analyser"
          />
        </div>

        <div className="action-grid">
          <button
            className="btn-forge"
            onClick={analyze}
            disabled={loading || !text.trim()}
          >
            {loading ? (
              <><span className="spinner" /> Analyse…</>
            ) : (
              "📊 Analyser l'Intention"
            )}
          </button>
          <button
            className="btn-clear"
            onClick={() => { setText(""); setResult(null); }}
            disabled={loading}
          >
            ✕
          </button>
        </div>
      </div>

      {/* ── RIGHT ── */}
      <div className="atelier-output-card">
        {result ? (
          <div className="analysis-results-wrap">
            {/* Primary intent card */}
            <div className="analysis-section">
              <div className="analysis-section-title">📊 Résultat</div>

              <div className="metric-grid" style={{ marginBottom: "1.5rem" }}>
                <div className="metric-card">
                  <div className="metric-label">Intention principale</div>
                  <div className="metric-value" style={{ fontSize: "1.1rem" }}>
                    {result.intent}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Confiance</div>
                  <div className="metric-value">
                    {(result.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="metric-bar-bg">
                    <div
                      className="metric-bar-fill"
                      style={{ width: `${Math.round(result.confidence * 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Score bars */}
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {sorted.map(([label, score], i) => (
                  <div className="score-row" key={label}>
                    <span className="score-label">{label}</span>
                    <div className="metric-bar-bg" style={{ flex: 1 }}>
                      <div
                        className={`metric-bar-fill${i === 0 ? " top" : ""}`}
                        style={{ width: `${Math.round(score * 100)}%` }}
                      />
                    </div>
                    <span className="score-pct">
                      {(score * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>

              {/* Meta */}
              <p className="meta-line" style={{ marginTop: "1rem" }}>
                Langue détectée :{" "}
                <strong>{result.source_language}</strong> · méthode :{" "}
                {result.method}
                {result.translated_text && (
                  <> · traduit : « {result.translated_text} »</>
                )}
              </p>
            </div>
          </div>
        ) : (
          <div className="atelier-empty-state">
            <div className="empty-crosshair" aria-hidden="true">◎</div>
            <div className="empty-title">Quelle est votre intention ?</div>
            <p className="empty-desc">
              CALIBRE classifie votre texte : débogage, génération, explication…
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
