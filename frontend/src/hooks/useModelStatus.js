import { useEffect, useState } from "react";
import { api } from "../api";

/** Interroge GET /status toutes les 4 s tant que les modèles chargent (le 1er chargement peut durer des minutes). */
export default function useModelStatus(enabled) {
  const [status, setStatus] = useState({ ready: true, models: {} });

  useEffect(() => {
    if (!enabled) return undefined;
    let timer;
    let cancelled = false;
    const poll = async () => {
      try {
        const { data } = await api.get("/status", { skipAuthRedirect: true });
        if (cancelled) return;
        setStatus(data);
        if (!data.ready) timer = setTimeout(poll, 4000);
      } catch (_) {
        if (!cancelled) timer = setTimeout(poll, 8000);
      }
    };
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [enabled]);

  return status;
}
