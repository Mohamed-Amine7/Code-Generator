import React, { useState } from "react";
import axios from "axios";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    try {
      const response = await axios.post("http://localhost:8000/analyze", {
        text: text,
        language: "fr", // ou "en" selon ce que tu veux
      });
      setResult(response.data);
    } catch (error) {
      console.error("Erreur analyse:", error);
      setResult(null);
    }
  };

  return (
    <div>
      <h1>CodeGen Frontend</h1>
      <textarea
        rows="5"
        cols="50"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Écris ton texte ici"
      />
      <br />
      <button onClick={handleAnalyze}>Analyser</button>

      {result && (
        <div>
          <h2>Résultat :</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>

          <p>
            <strong>Intention :</strong> {result.intent[0].label}
          </p>
          <p>
            <strong>Score :</strong> {(result.intent[0].score * 100).toFixed(2)}%
          </p>
        </div>
      )}
    </div>
  );
}

export default App;
