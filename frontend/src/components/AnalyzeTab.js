import React, { useState } from "react";
import { api, errorMessage } from "../api";
import { useToast } from "../context/ToastContext";
import CodeBlock from "./CodeBlock";

export default function AnalyzeTab() {
  const { notify } = useToast();
  const [code, setCode]   = useState("");
  const [level, setLevel] = useState("beginner");
  const [res, setRes]     = useState({});
  const [activeItem, setActiveItem] = useState(null);
  const [loadingMap, setLoadingMap] = useState({
    feedback: false,
    explanation: false,
    tests: false,
  });

  const runSingle = async (key) => {
    if (!code.trim()) return notify("Collez du code à analyser !", "error");
    setLoadingMap((m) => ({ ...m, [key]: true }));
    setActiveItem(key);
    try {
      let data;
      if (key === "feedback") {
        const r = await api.post("/code/feedback", { code, language: "python" });
        data = r.data;
      } else if (key === "explanation") {
        const r = await api.post("/code/explain", { code, level });
        data = r.data;
      } else if (key === "tests") {
        const r = await api.post("/code/tests", { code });
        data = r.data;
      }
      setRes((prev) => ({ ...prev, [key]: data }));
    } catch (err) {
      notify(`${key} : ${errorMessage(err)}`, "error");
    } finally {
      setLoadingMap((m) => ({ ...m, [key]: false }));
      setActiveItem(null);
    }
  };

  const runAllProgressive = async () => {
    if (!code.trim()) return notify("Collez du code à analyser !", "error");
    setActiveItem("all");
    setLoadingMap({ feedback: true, explanation: true, tests: true });

    try {
      const fb = await api.post("/code/feedback", { code, language: "python" });
      setRes((prev) => ({ ...prev, feedback: fb.data }));
    } catch (err) {
      notify(`Feedback : ${errorMessage(err)}`, "error");
    } finally {
      setLoadingMap((m) => ({ ...m, feedback: false }));
    }

    try {
      const exp = await api.post("/code/explain", { code, level });
      setRes((prev) => ({ ...prev, explanation: exp.data }));
    } catch (err) {
      notify(`Explication : ${errorMessage(err)}`, "error");
    } finally {
      setLoadingMap((m) => ({ ...m, explanation: false }));
    }

    try {
      const tst = await api.post("/code/tests", { code });
      setRes((prev) => ({ ...prev, tests: tst.data }));
    } catch (err) {
      notify(`Tests : ${errorMessage(err)}`, "error");
    } finally {
      setLoadingMap((m) => ({ ...m, tests: false }));
      setActiveItem(null);
    }
  };

  const isAnyLoading = Object.values(loadingMap).some(Boolean);
  const hasResults   = Object.keys(res).length > 0;

  return (
    <div className="workbench-grid">
      {/* ── LEFT ── */}
      <div className="atelier-input-card">
        <div className="panel-header-editorial">
          <span className="section-label">02 / CODE À ANALYSER</span>
        </div>

        <div className="input-options-row">
          <label htmlFor="analyze-level" className="sr-only">
            Niveau d'explication
          </label>
          <select
            id="analyze-level"
            className="calibre-select"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            disabled={isAnyLoading}
          >
            <option value="beginner">Niveau — Débutant</option>
            <option value="intermediate">Niveau — Intermédiaire</option>
            <option value="expert">Niveau — Expert</option>
          </select>
        </div>

        <div className="prompt-area-wrap">
          <textarea
            className="calibre-textarea"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            rows={10}
            maxLength={20000}
            placeholder="Collez votre code ici…"
            disabled={isAnyLoading}
            aria-label="Code à analyser"
          />
        </div>

        {/* Action grid */}
        <div className="analyze-action-grid">
          <button
            className="btn-forge"
            onClick={runAllProgressive}
            disabled={isAnyLoading || !code.trim()}
            style={{ gridColumn: "1 / -1" }}
            title="Lancer la revue, l'explication et les tests en parallèle"
          >
            {activeItem === "all" ? (
              <><span className="spinner" /> Analyse complète…</>
            ) : (
              "⚡ Analyse Complète"
            )}
          </button>

          <button
            className="btn-tool"
            onClick={() => runSingle("feedback")}
            disabled={isAnyLoading || !code.trim()}
          >
            {loadingMap.feedback ? (
              <><span className="spinner" /> Revue…</>
            ) : (
              "💡 Revue & Bugs"
            )}
          </button>

          <button
            className="btn-tool"
            onClick={() => runSingle("explanation")}
            disabled={isAnyLoading || !code.trim()}
          >
            {loadingMap.explanation ? (
              <><span className="spinner" /> Explication…</>
            ) : (
              "📚 Expliquer"
            )}
          </button>

          <button
            className="btn-tool"
            onClick={() => runSingle("tests")}
            disabled={isAnyLoading || !code.trim()}
          >
            {loadingMap.tests ? (
              <><span className="spinner" /> Génération…</>
            ) : (
              "🧪 Générer Tests"
            )}
          </button>

          <button
            className="btn-clear"
            onClick={() => { setCode(""); setRes({}); }}
            disabled={isAnyLoading}
            style={{ gridColumn: "1 / -1" }}
          >
            ✕ Effacer
          </button>
        </div>
      </div>

      {/* ── RIGHT ── */}
      <div className="atelier-output-card">
        {hasResults || isAnyLoading ? (
          <div className="analysis-results-wrap">

            {/* Feedback */}
            {loadingMap.feedback && !res.feedback && (
              <div className="analysis-section">
                <div className="analysis-section-title">
                  <span className="spinner" /> 💡 Revue en cours…
                </div>
                <div className="explanation-card" style={{ opacity: 0.5 }}>
                  <p>Inspection de la qualité du code…</p>
                </div>
              </div>
            )}
            {res.feedback && (
              <div className="analysis-section">
                <div className="analysis-section-title">
                  💡 Retour &amp; Revue
                  {res.feedback.cached && (
                    <span className="verify-badge verify-passed" style={{ marginLeft: 8 }}>
                      ⚡ Cache
                    </span>
                  )}
                </div>
                <div className="explanation-card">
                  <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                    {res.feedback.feedback}
                  </pre>
                </div>
              </div>
            )}

            {/* Explanation */}
            {loadingMap.explanation && !res.explanation && (
              <div className="analysis-section">
                <div className="analysis-section-title">
                  <span className="spinner" /> 📚 Explication en cours…
                </div>
                <div className="explanation-card" style={{ opacity: 0.5 }}>
                  <p>Génération de l'explication pas à pas…</p>
                </div>
              </div>
            )}
            {res.explanation && (
              <div className="analysis-section">
                <div className="analysis-section-title">
                  📚 Explication ({level})
                  {res.explanation.cached && (
                    <span className="verify-badge verify-passed" style={{ marginLeft: 8 }}>
                      ⚡ Cache
                    </span>
                  )}
                </div>
                <div className="explanation-card">
                  <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                    {res.explanation.explanation}
                  </pre>
                </div>
              </div>
            )}

            {/* Tests */}
            {loadingMap.tests && !res.tests && (
              <div className="analysis-section">
                <div className="analysis-section-title">
                  <span className="spinner" /> 🧪 Tests en cours…
                </div>
                <div className="explanation-card" style={{ opacity: 0.5 }}>
                  <p>Génération des tests unitaires…</p>
                </div>
              </div>
            )}
            {res.tests && (
              <div className="analysis-section">
                <div className="analysis-section-title">
                  🧪 Tests Unitaires
                  {res.tests.cached && (
                    <span className="verify-badge verify-passed" style={{ marginLeft: 8 }}>
                      ⚡ Cache
                    </span>
                  )}
                </div>
                <div className="editor-frame">
                  <CodeBlock code={res.tests.tests} language="python" />
                </div>
              </div>
            )}

          </div>
        ) : (
          <div className="atelier-empty-state">
            <div className="empty-crosshair" aria-hidden="true">◎</div>
            <div className="empty-title">Les résultats apparaîtront ici.</div>
            <p className="empty-desc">
              Collez votre code et choisissez une analyse ou lancez l'analyse complète.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
