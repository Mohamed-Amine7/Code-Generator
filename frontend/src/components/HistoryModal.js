import React, { useCallback, useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { useToast } from "../context/ToastContext";

const PAGE = 20;

export default function HistoryModal({ onClose, onSelect }) {
  const { notify } = useToast();
  const [items, setItems]           = useState([]);
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [hasMore, setHasMore]       = useState(false);
  const [loading, setLoading]       = useState(false);

  const load = useCallback(
    async (skip) => {
      setLoading(true);
      try {
        const { data } = await api.get("/history", {
          params: { skip, limit: PAGE, favorites_only: favoritesOnly },
        });
        setItems((prev) => (skip === 0 ? data : [...prev, ...data]));
        setHasMore(data.length === PAGE);
      } catch (err) {
        notify(errorMessage(err, "Impossible de charger l'historique"), "error");
      } finally {
        setLoading(false);
      }
    },
    [favoritesOnly, notify]
  );

  useEffect(() => { load(0); }, [load]);

  // Close on Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const remove = async (e, id) => {
    e.stopPropagation();
    try {
      await api.delete(`/history/${id}`);
      setItems((p) => p.filter((i) => i.id !== id));
    } catch (err) {
      notify(errorMessage(err), "error");
    }
  };

  const favorite = async (e, id) => {
    e.stopPropagation();
    try {
      const { data } = await api.patch(`/history/${id}/favorite`);
      setItems((p) =>
        favoritesOnly && !data.is_favorite
          ? p.filter((i) => i.id !== id)
          : p.map((i) => (i.id === id ? data : i))
      );
    } catch (err) {
      notify(errorMessage(err), "error");
    }
  };

  return (
    <div
      className="drawer-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Ledger des générations"
    >
      <div className="drawer-ledger" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="drawer-header">
          <div className="drawer-title">
            <span className="section-label" style={{ fontSize: "0.7rem" }}>
              LEDGER
            </span>
            Générations
          </div>
          <button
            className="btn-control"
            onClick={onClose}
            aria-label="Fermer le Ledger"
          >
            ✕
          </button>
        </div>

        {/* Filter */}
        <div className="drawer-filter">
          <label className="calibre-check">
            <input
              type="checkbox"
              checked={favoritesOnly}
              onChange={(e) => setFavoritesOnly(e.target.checked)}
            />
            Favoris uniquement
          </label>
        </div>

        {/* List */}
        <div className="drawer-body">
          {items.length === 0 && !loading ? (
            <div className="atelier-empty-state" style={{ padding: "3rem 1rem" }}>
              <div className="empty-crosshair">◎</div>
              <div className="empty-title" style={{ fontSize: "1rem" }}>
                {favoritesOnly ? "Aucun favori." : "Aucune génération."}
              </div>
              <p className="empty-desc" style={{ fontSize: "0.8rem" }}>
                {favoritesOnly
                  ? "Marquez des générations comme favorites."
                  : "Générez du code pour alimenter le Ledger."}
              </p>
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="ledger-item"
                onClick={() => onSelect(item)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && onSelect(item)}
              >
                <div className="ledger-item-top">
                  <span className="lang-tag" style={{ fontSize: "0.65rem" }}>
                    {item.language}
                  </span>
                  <span className="ledger-time">
                    {item.timestamp
                      ? new Date(item.timestamp).toLocaleString("fr-FR", {
                          dateStyle: "short",
                          timeStyle: "short",
                        })
                      : ""}
                  </span>
                </div>
                <p className="ledger-query">{item.query}</p>
                <div className="ledger-actions">
                  <button
                    className="btn-tool"
                    onClick={(e) => favorite(e, item.id)}
                    style={{ fontSize: "0.75rem" }}
                  >
                    {item.is_favorite ? "★ Favori" : "☆ Favori"}
                  </button>
                  <button
                    className="btn-tool"
                    onClick={(e) => remove(e, item.id)}
                    style={{ fontSize: "0.75rem", color: "var(--status-red)" }}
                  >
                    🗑 Suppr.
                  </button>
                </div>
              </div>
            ))
          )}

          {hasMore && (
            <button
              className="btn-clear"
              disabled={loading}
              onClick={() => load(items.length)}
              style={{ width: "100%", marginTop: "0.5rem" }}
            >
              {loading ? "Chargement…" : "Voir plus"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
