import './KrayaCard.css';

/* ============================================
   KrayaCard — обёртка с clip-path формой
   ============================================
   variant="info"         — скос верхний-левый 12px + SVG обводка
   variant="info-bottom"  — скос верхний-левый + нижний-правый 14px, БЕЗ обводки
   variant="topHeroes"    — скос верхний-левый 14px + SVG обводка

   Props:
     variant    — 'info' | 'info-bottom' | 'topHeroes'
     frameUrl   — URL SVG обводки (опционально)
   ============================================ */

export default function KrayaCard({ variant = 'info', frameUrl, children }) {
  return (
    <div className={`krayaCardRoot krayaCardRoot--${variant}`}>
      {children}

      {/* SVG обводка — только если указан frameUrl */}
      {frameUrl && (
        <img
          className="krayaCardFrame"
          src={frameUrl}
          alt=""
          aria-hidden="true"
          draggable="false"
        />
      )}
    </div>
  );
}
