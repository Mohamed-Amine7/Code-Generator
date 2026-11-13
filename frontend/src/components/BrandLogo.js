import React from "react";

export default function BrandLogo({ size = 32, subtitle = true }) {
  const px = typeof size === "number" ? size : size === "compact" ? 26 : 32;
  return (
    <div className="calibre-brand">
      <svg
        className="calibre-mark"
        width={px}
        height={px}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Cadran d'instrument de mesure / Calibre */}
        <rect x="1" y="1" width="30" height="30" rx="3" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.4" />
        <circle cx="16" cy="16" r="8" stroke="currentColor" strokeWidth="1.2" strokeDasharray="2 2" strokeOpacity="0.6" />
        {/* Réticule de précision */}
        <line x1="16" y1="4" x2="16" y2="8" stroke="currentColor" strokeWidth="1.5" />
        <line x1="16" y1="24" x2="16" y2="28" stroke="currentColor" strokeWidth="1.5" />
        <line x1="4" y1="16" x2="8" y2="16" stroke="currentColor" strokeWidth="1.5" />
        <line x1="24" y1="16" x2="28" y2="16" stroke="currentColor" strokeWidth="1.5" />
        {/* Point focal vif (Acid Lime) */}
        <rect x="14" y="14" width="4" height="4" fill="var(--accent-vivid)" />
      </svg>
      <div className="calibre-nametag">
        <div className="calibre-wordmark">
          <span>CALIBRE</span>
          <span className="calibre-dot">.</span>
          <span className="calibre-version">v2</span>
        </div>
        {subtitle && (
          <span className="calibre-subline">ATELIER D'INGÉNIERIE LOGICIELLE</span>
        )}
      </div>
    </div>
  );
}
