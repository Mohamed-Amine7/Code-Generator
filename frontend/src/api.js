import axios from "axios";

export const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// withCredentials : le JWT voyage dans un cookie httpOnly (jamais lisible par le JavaScript de la page)
export const api = axios.create({ baseURL: API_URL, withCredentials: true });

// Session expirée (30 min) -> on prévient AuthContext, sauf pour les appels marqués skipAuthRedirect
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && !error.config?.skipAuthRedirect) {
      window.dispatchEvent(new Event("auth:expired"));
    }
    return Promise.reject(error);
  }
);

export function errorMessage(error, fallback = "Something went wrong") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg.replace(/^Value error, /, "");
  if (error?.response?.status === 429) return "Too many requests, slow down a little.";
  return error?.message || fallback;
}

/** Génération en streaming (SSE via fetch). Renvoie l'événement final {code, id, cached, ...}. */
export async function streamGenerate(body, { onToken, signal }) {
  const res = await fetch(`${API_URL}/generate/stream`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (res.status === 401) {
    window.dispatchEvent(new Event("auth:expired"));
    throw new Error("Session expired");
  }
  if (!res.ok) {
    let detail = "Generation failed";
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : data.detail?.[0]?.msg || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let final = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop();
    for (const part of parts) {
      if (!part.startsWith("data: ")) continue;
      const evt = JSON.parse(part.slice(6));
      if (evt.error) throw new Error(evt.error);
      if (evt.token) onToken(evt.token);
      if (evt.done) final = evt;
    }
  }
  return final;
}
