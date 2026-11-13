import React, { useEffect, useRef, useState } from "react";
import { api, errorMessage, streamGenerate } from "../api";
import { useToast } from "../context/ToastContext";
import CodeBlock from "./CodeBlock";

const PLACEHOLDER_PROMPTS = [
  "Décrivez le code que CALIBRE doit forger…",
  "Ex. : « Trier une liste en Python »",
  "Ex. : « API REST avec FastAPI et SQLAlchemy »",
  "Ex. : « Calculatrice en Java »",
  "Ex. : « Scraper web avec BeautifulSoup »",
];

const STEPS = ["01 Comprendre", "02 Écrire", "03 Analyser"];

export default function GenerateTab({ initial, onInitialConsumed }) {
  const { notify } = useToast();
  const [text, setText]       = useState("");
  const [language, setLanguage] = useState("python");
  const [verify, setVerify]   = useState(false);
  const [prompts, setPrompts] = useState([]);
  const [result, setResult]   = useState(null);
  const [streaming, setStreaming] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied]   = useState(false);
  const [phIdx, setPhIdx]     = useState(0);
  const [activeStep, setActiveStep] = useState(0);
  const abortRef = useRef(null);

  // Rotate placeholder text
  useEffect(() => {
    const id = setInterval(
      () => setPhIdx((i) => (i + 1) % PLACEHOLDER_PROMPTS.length),
      3000
    );
    return () => clearInterval(id);
  }, []);

  // Animate steps during loading
  useEffect(() => {
    if (!loading) { setActiveStep(0); return; }
    const id = setInterval(
      () => setActiveStep((s) => (s < STEPS.length - 1 ? s + 1 : s)),
      2800
    );
    return () => clearInterval(id);
  }, [loading]);

  useEffect(() => {
    api
      .get("/prompts", { skipAuthRedirect: true })
      .then((r) => setPrompts(r.data))
      .catch(() => {});
  }, []);

  // Load from history
  useEffect(() => {
    if (!initial) return;
    setText(initial.query);
    setLanguage(initial.language || "python");
    setResult({
      code: initial.generated_code,
      id: initial.id,
      cached: true,
      explanation: initial.explanation || "",
    });
    onInitialConsumed();
  }, [initial, onInitialConsumed]);

  // Keyboard shortcut Ctrl+Enter
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        if (!loading && text.trim()) generate();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, text, language, verify]);

  const generate = async (regenerate = false) => {
    if (!text.trim()) return notify("Décrivez d'abord ce que vous voulez générer !", "error");
    setLoading(true);
    setResult(null);
    setStreaming("");
    abortRef.current = new AbortController();
    try {
      if (verify) {
        const { data } = await api.post("/generate", {
          text,
          language,
          verify: true,
          regenerate,
        });
        setResult({
          code: data.generated_code,
          id: data.id,
          cached: data.cached,
          verification: data.verification,
          explanation: data.explanation,
        });
      } else {
        const final = await streamGenerate(
          { text, language, regenerate },
          {
            onToken: (t) => setStreaming((s) => s + t),
            signal: abortRef.current.signal,
          }
        );
        if (final)
          setResult({
            code: final.code,
            id: final.id,
            cached: final.cached,
            explanation: "",
          });
      }
    } catch (err) {
      if (err.name === "AbortError")
        notify("Génération interrompue", "info");
      else
        notify(errorMessage(err, "Erreur de génération"), "error");
    } finally {
      setStreaming("");
      setLoading(false);
    }
  };

  const explain = async () => {
    try {
      const { data } = await api.post("/code/explain", {
        code: result.code,
        level: "beginner",
      });
      setResult((r) => ({ ...r, explanation: data.explanation }));
    } catch (err) {
      notify(errorMessage(err, "Impossible d'expliquer le code"), "error");
    }
  };

  const copy = () => {
    navigator.clipboard
      .writeText(result.code)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => notify("Copie impossible", "error"));
  };

  const handlePDF = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== "application/pdf")
      return notify("Fichier PDF uniquement !", "error");
    try {
      const pdfjs  = await import("pdfjs-dist");
      const worker = await import("pdfjs-dist/build/pdf.worker.entry");
      pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
      const pdf = await pdfjs
        .getDocument({ data: new Uint8Array(await file.arrayBuffer()) })
        .promise;
      let content = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        content +=
          (await page.getTextContent()).items.map((it) => it.str).join(" ") +
          "\n";
      }
      setText(content.trim().slice(0, 1000));
      if (content.length > 1000)
        notify("Texte PDF tronqué à 1000 caractères", "info");
    } catch {
      notify("Impossible de lire ce PDF", "error");
    }
  };

  const clear = () => {
    abortRef.current?.abort();
    setText("");
    setResult(null);
    setStreaming("");
  };

  const shown = loading ? streaming : result?.code;
  const v     = result?.verification;

  return (
    <div className="workbench-grid">
      {/* ── LEFT : INPUT ── */}
      <div className="atelier-input-card">
        <div className="panel-header-editorial">
          <span className="section-label">01 / REQUÊTE</span>
          <span className="section-hint">Ctrl+Entrée pour générer</span>
        </div>

        {/* Language selector */}
        <div className="input-options-row">
          <label htmlFor="gen-lang" className="sr-only">
            Langage cible
          </label>
          <select
            id="gen-lang"
            className="calibre-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={loading}
          >
            <option value="python">Python</option>
            <option value="java">Java</option>
          </select>
        </div>

        {/* PDF import */}
        <label className="pdf-strip" title="Importer un fichier PDF">
          <input
            type="file"
            accept="application/pdf"
            onChange={handlePDF}
            disabled={loading}
            aria-label="Importer un PDF"
          />
          📄 Importer un cahier des charges PDF
        </label>

        {/* Main textarea */}
        <div className="prompt-area-wrap">
          <textarea
            className="calibre-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            maxLength={1000}
            placeholder={PLACEHOLDER_PROMPTS[phIdx]}
            disabled={loading}
            aria-label="Description du code à générer"
          />
        </div>

        {/* Verify checkbox (Python only) */}
        {language === "python" && (
          <label className="calibre-check">
            <input
              type="checkbox"
              checked={verify}
              onChange={(e) => setVerify(e.target.checked)}
              disabled={loading}
            />
            Vérifier avec tests sandbox (sans streaming)
          </label>
        )}

        {/* Actions */}
        <div className="action-grid">
          {loading && !verify ? (
            <button
              className="btn-clear"
              onClick={() => abortRef.current?.abort()}
            >
              ⬛ Arrêter
            </button>
          ) : (
            <button
              className="btn-forge"
              onClick={() => generate(false)}
              disabled={loading || !text.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner" /> CALIBRE forge…
                </>
              ) : (
                "⚡ Forger le Code"
              )}
            </button>
          )}
          <button className="btn-clear" onClick={clear} aria-label="Effacer">
            ✕
          </button>
        </div>

        {/* Quick prompts */}
        {prompts.length > 0 && (
          <>
            <div className="examples-title">EXEMPLES RAPIDES</div>
            <div className="examples-pills">
              {prompts.map((p) => (
                <button
                  key={p}
                  className="prompt-pill-btn"
                  onClick={() => {
                    setText(p);
                    setLanguage(/java/i.test(p) ? "java" : "python");
                  }}
                  disabled={loading}
                >
                  {p}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* ── RIGHT : OUTPUT ── */}
      <div className="atelier-output-card">
        {loading && (
          <div className="progress-stepper" aria-live="polite">
            {STEPS.map((s, i) => (
              <span
                key={s}
                className={`step-item${i === activeStep ? " active" : i < activeStep ? " done" : ""}`}
              >
                {s}
              </span>
            ))}
          </div>
        )}

        {shown ? (
          <>
            <div className="code-output-header">
              <div className="code-meta-badges">
                <span className="lang-tag">{language.toUpperCase()}</span>
                {v && (
                  <span className={`verify-badge verify-${v.status}`}>
                    tests : {v.status}
                  </span>
                )}
                {result?.cached && (
                  <span className="verify-badge verify-passed">⚡ Cache</span>
                )}
              </div>
              {!loading && (
                <div className="code-toolbar">
                  <button className="btn-tool" onClick={copy}>
                    {copied ? "✔ Copié !" : "📋 Copier"}
                  </button>
                  <button className="btn-tool" onClick={() => generate(true)}>
                    🔄 Regénérer
                  </button>
                </div>
              )}
            </div>

            <div className="editor-frame">
              <CodeBlock code={shown} language={language} isStreaming={loading} />
            </div>

            {!loading && result && (
              <>
                {v?.failures?.length > 0 && (
                  <pre className="code-raw">{v.failures.join("\n\n")}</pre>
                )}
                {result.explanation ? (
                  <div className="explanation-card">
                    <div className="explanation-label">📖 Explication</div>
                    <p style={{ whiteSpace: "pre-wrap" }}>{result.explanation}</p>
                  </div>
                ) : (
                  <button className="btn-tool" onClick={explain}>
                    📖 Expliquer ce code
                  </button>
                )}
              </>
            )}
          </>
        ) : (
          <div className="atelier-empty-state">
            <div className="empty-crosshair" aria-hidden="true">◎</div>
            <div className="empty-title">La forge attend votre requête.</div>
            <p className="empty-desc">
              Décrivez ce que vous voulez créer — CALIBRE le forgera.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
