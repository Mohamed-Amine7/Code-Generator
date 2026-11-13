import React, { useEffect, useState } from "react";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Zap,
  Eye,
  MessageSquare,
  FileCheck,
  Code,
} from "lucide-react";
import { api, errorMessage } from "../api";
import { useToast } from "../context/ToastContext";

const EXAMPLE = `def calculate_fibonacci(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a,b=0,1
    for i in range(2,n+1):
        a,b=b,a+b
    return b

def main():
    result=calculate_fibonacci(10)
    print(result)

main()`;

const iconFor = (type) => {
  switch (type) {
    case "error":      return <XCircle      className="icon icon-red"    size={15} />;
    case "warning":    return <AlertTriangle className="icon icon-yellow" size={15} />;
    case "info":       return <Info          className="icon icon-blue"   size={15} />;
    case "suggestion": return <MessageSquare className="icon icon-purple" size={15} />;
    default:           return <Info          className="icon icon-gray"   size={15} />;
  }
};

function DiffView({ diff }) {
  if (!diff) return null;
  return (
    <div className="diff-view">
      {diff.split("\n").map((line, i) => {
        const cls =
          line.startsWith("+") && !line.startsWith("+++")
            ? "diff-add"
            : line.startsWith("-") && !line.startsWith("---")
            ? "diff-del"
            : "diff-ctx";
        return (
          <span key={i} className={cls}>
            {line || " "}
          </span>
        );
      })}
    </div>
  );
}

export default function FeedbackSystem() {
  const { notify } = useToast();
  const [code, setCode]           = useState("");
  const [annotations, setAnnotations] = useState([]);
  const [validation, setValidation]   = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isCorrecting, setIsCorrecting] = useState(false);
  const [correction, setCorrection] = useState(null);
  const [feedbackType, setFeedbackType] = useState("");
  const [comment, setComment]     = useState("");
  const [rating, setRating]       = useState(0);

  useEffect(() => { setCode(EXAMPLE); }, []);

  const validate = async () => {
    setIsValidating(true);
    setAnnotations([]);
    try {
      const { data } = await api.post("/api/feedback/validate", {
        code,
        language: "python",
      });
      setAnnotations(data.annotations || []);
      setValidation(data);
    } catch (err) {
      notify(errorMessage(err, "Erreur de validation"), "error");
    } finally {
      setIsValidating(false);
    }
  };

  const autoCorrect = async () => {
    setIsCorrecting(true);
    try {
      const { data } = await api.post("/api/correction/", {
        code,
        language: "python",
      });
      setCorrection(data);
      if (!data.changed) notify("Rien à corriger automatiquement", "info");
    } catch (err) {
      notify(errorMessage(err, "Erreur de correction"), "error");
    } finally {
      setIsCorrecting(false);
    }
  };

  const applyCorrection = () => {
    setCode(correction.corrected_code);
    setCorrection(null);
    setAnnotations([]);
    setValidation(null);
  };

  const submitFeedback = async () => {
    try {
      await api.post("/api/feedback/feedback", {
        code_id: "temp-code-id",
        type: feedbackType,
        comment: comment || null,
        rating: rating >= 1 ? rating : null,
      });
      notify("Feedback enregistré !", "success");
      setComment("");
      setRating(0);
      setFeedbackType("");
    } catch (err) {
      notify(errorMessage(err, "Erreur envoi feedback"), "error");
    }
  };

  const lineAnns = (n) => annotations.filter((a) => a.line === n);
  const score      = validation?.quality_score ?? 0;
  const scoreColor =
    score >= 8 ? "var(--status-green)" : score >= 6 ? "var(--status-yellow)" : "var(--status-red)";
  const lines = code.split("\n");

  return (
    <div className="workbench-grid">
      {/* ── LEFT : CODE EDITOR + RESULTS ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>

        {/* Editor card */}
        <div className="atelier-input-card">
          <div className="panel-header-editorial">
            <span className="section-label">04 / QUALITÉ &amp; LINTER</span>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                className="btn-forge"
                onClick={validate}
                disabled={isValidating || !code.trim()}
              >
                {isValidating ? (
                  <><span className="spinner" /> Validation…</>
                ) : (
                  <><Eye size={14} /> Valider</>
                )}
              </button>
              <button
                className="btn-tool"
                onClick={autoCorrect}
                disabled={isCorrecting || !code.trim()}
              >
                {isCorrecting ? (
                  <><span className="spinner" /> Correction…</>
                ) : (
                  <><Zap size={14} /> Corriger</>
                )}
              </button>
            </div>
          </div>

          {/* Editor with line numbers */}
          <div className="line-editor-wrap">
            <div className="line-gutter" aria-hidden="true">
              {lines.map((_, idx) => {
                const has = lineAnns(idx + 1).length > 0;
                return (
                  <div
                    key={idx}
                    className={`lineNumRow${has ? " hot" : ""}`}
                    title={
                      lineAnns(idx + 1)
                        .map((a) => a.message)
                        .join("\n") || undefined
                    }
                  >
                    <span className="lineNum">{idx + 1}</span>
                    {has && <span className="pulseDot" aria-hidden="true" />}
                  </div>
                );
              })}
            </div>
            <textarea
              className="calibre-textarea codeArea"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
              rows={Math.max(10, lines.length)}
              aria-label="Code à valider"
            />
          </div>
        </div>

        {/* Quality result */}
        {validation && (
          <div className="atelier-output-card">
            <div className="analysis-section">
              <div className="analysis-section-title">
                {validation.valid ? (
                  <CheckCircle className="icon icon-green" size={16} />
                ) : (
                  <XCircle className="icon icon-red" size={16} />
                )}
                {validation.valid ? " Syntaxe valide" : " Erreur de syntaxe"}
                <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Qualité
                  </span>
                  <span style={{ fontWeight: 700, color: scoreColor }}>
                    {score}/10
                  </span>
                  <div
                    className="metric-bar-bg"
                    style={{ width: 80 }}
                  >
                    <div
                      className="metric-bar-fill"
                      style={{
                        width: `${Math.max(0, Math.min(100, score * 10))}%`,
                        background: scoreColor,
                      }}
                    />
                  </div>
                </span>
              </div>

              {annotations.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginTop: "0.75rem" }}>
                  {annotations.map((a, i) => (
                    <div key={i} className="fixRow">
                      {iconFor(a.type)}
                      <span>
                        {a.line ? `L${a.line} — ` : ""}
                        {a.message}{" "}
                        <em style={{ opacity: 0.5, fontSize: "0.75em" }}>
                          [{a.source}]
                        </em>
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Correction diff card */}
        {correction && correction.changed && (
          <div className="atelier-output-card" style={{ borderColor: "var(--status-green)" }}>
            <div className="analysis-section">
              <div className="analysis-section-title">
                <Zap size={15} /> Code corrigé
                <button
                  className="btn-tool"
                  onClick={applyCorrection}
                  style={{ marginLeft: "auto" }}
                >
                  <CheckCircle size={13} /> Appliquer
                </button>
              </div>
              <pre className="code-raw" style={{ marginTop: "0.5rem" }}>
                {correction.corrected_code}
              </pre>
              <DiffView diff={correction.diff} />
              <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                {correction.fixes.map((fix, i) => (
                  <div key={i} className="fixRow">
                    <CheckCircle size={13} className="icon icon-green" />
                    <span>{fix}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── RIGHT : FEEDBACK FORM ── */}
      <div className="atelier-output-card">
        {validation ? (
          <div className="analysis-section">
            <div className="panel-header-editorial">
              <span className="section-label">04B / RETOUR UTILISATEUR</span>
            </div>

            <div className="auth-field" style={{ marginTop: "1rem" }}>
              <label htmlFor="fb-type">Type de feedback</label>
              <select
                id="fb-type"
                className="calibre-select"
                value={feedbackType}
                onChange={(e) => setFeedbackType(e.target.value)}
              >
                <option value="">— Choisir —</option>
                <option value="positive">👍 Positif</option>
                <option value="negative">👎 Négatif</option>
                <option value="suggestion">💡 Suggestion</option>
              </select>
            </div>

            <div className="auth-field">
              <label htmlFor="fb-comment">Commentaire</label>
              <textarea
                id="fb-comment"
                className="calibre-textarea"
                rows={5}
                maxLength={2000}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Votre commentaire…"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="fb-rating">Note (1 à 5)</label>
              <input
                id="fb-rating"
                type="number"
                min="0"
                max="5"
                className="calibre-select"
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
              />
            </div>

            <button
              className="btn-forge"
              onClick={submitFeedback}
              disabled={!feedbackType}
              style={{ width: "100%", marginTop: "1rem" }}
            >
              Envoyer le feedback
            </button>
          </div>
        ) : (
          <div className="atelier-empty-state">
            <div className="empty-crosshair" aria-hidden="true">◎</div>
            <div className="empty-title">Validez d'abord le code.</div>
            <p className="empty-desc">
              Cliquez sur « Valider » pour lancer l'analyse statique, puis donnez votre retour.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
