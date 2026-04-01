import React from 'react';

const W = 320;
const H = 320;
const PAD = 32;

function mapPoint(re, im, xMin, xMax, yMin, yMax) {
  const pw = W - 2 * PAD;
  const ph = H - 2 * PAD;
  const sx = PAD + ((re - xMin) / (xMax - xMin)) * pw;
  const sy = PAD + ((yMax - im) / (yMax - yMin)) * ph;
  return [sx, sy];
}

function circlePolylinePoints(xMin, xMax, yMin, yMax, radius, segments = 120) {
  const pts = [];
  for (let i = 0; i <= segments; i++) {
    const t = (i / segments) * Math.PI * 2;
    const re = radius * Math.cos(t);
    const im = radius * Math.sin(t);
    const [sx, sy] = mapPoint(re, im, xMin, xMax, yMin, yMax);
    pts.push(`${sx},${sy}`);
  }
  return pts.join(' ');
}

/**
 * variant "z" — jednotková kružnice a póly z
 * variant "s" — polocha Re(s)<0 a póly s
 */
function ComplexPolePlot({ variant, poles, theme }) {
  const isDark = theme === 'dark';
  const pts = (poles || []).map((p) => ({ re: Number(p.re), im: Number(p.im) }));

  let xMin;
  let xMax;
  let yMin;
  let yMax;

  if (variant === 'z') {
    const maxMod = pts.length ? pts.reduce((m, p) => Math.max(m, Math.hypot(p.re, p.im)), 0) : 0;
    const L = Math.max(1.08, maxMod * 1.08, 1.08);
    xMin = -L;
    xMax = L;
    yMin = -L;
    yMax = L;
  } else if (!pts.length) {
    xMin = -2;
    xMax = 0.5;
    yMin = -1.5;
    yMax = 1.5;
  } else {
    let minRe = Infinity;
    let maxRe = -Infinity;
    let minIm = Infinity;
    let maxIm = -Infinity;
    for (const p of pts) {
      minRe = Math.min(minRe, p.re);
      maxRe = Math.max(maxRe, p.re);
      minIm = Math.min(minIm, p.im);
      maxIm = Math.max(maxIm, p.im);
    }
    const span = Math.max(Math.abs(minRe), Math.abs(maxRe), Math.abs(minIm), Math.abs(maxIm), 0.5);
    const pad = span * 0.12 + 0.08;
    xMin = Math.min(minRe - pad, -pad);
    xMax = Math.max(maxRe + pad, pad * 0.75);
    yMin = minIm - pad;
    yMax = maxIm + pad;
  }

  const axisStroke = isDark ? '#94a3b8' : '#64748b';
  const unitStroke = isDark ? '#38bdf8' : '#0369a1';
  const unitStrokeHi = isDark ? '#7dd3fc' : '#0ea5e9';
  const lhpFill = isDark ? 'rgba(16, 185, 129, 0.12)' : 'rgba(16, 185, 129, 0.18)';
  const poleIn = isDark ? '#34d399' : '#059669';
  const poleOut = isDark ? '#fb7185' : '#e11d48';
  const numFill = isDark ? '#f1f5f9' : '#0f172a';
  const axisLabelFill = isDark ? '#cbd5e1' : '#475569';

  const [ox0, oy0] = mapPoint(0, 0, xMin, xMax, yMin, yMax);
  const [ox1] = mapPoint(xMax, 0, xMin, xMax, yMin, yMax);
  const [ox2] = mapPoint(xMin, 0, xMin, xMax, yMin, yMax);
  const [rx1, ry1] = mapPoint(1, 0, xMin, xMax, yMin, yMax);
  const [, iy1] = mapPoint(0, 1, xMin, xMax, yMin, yMax);
  const [, oyB] = mapPoint(0, yMin, xMin, xMax, yMin, yMax);
  const [, oyD] = mapPoint(0, yMax, xMin, xMax, yMin, yMax);
  const showRe1 = xMin <= 1 + 1e-9 && xMax >= 1 - 1e-9;
  const showIm1 = yMin <= 1 + 1e-9 && yMax >= 1 - 1e-9;
  const showReNeg1 = xMin <= -1 + 1e-9 && xMax >= -1 - 1e-9;
  const showImNeg1 = yMin <= -1 + 1e-9 && yMax >= -1 - 1e-9;
  const [rxN1, ryN1] = mapPoint(-1, 0, xMin, xMax, yMin, yMax);
  const [, iyN1] = mapPoint(0, -1, xMin, xMax, yMin, yMax);
  const tick = 7;

  const reName = variant === 'z' ? 'Re z' : 'Re s';
  const imName = variant === 'z' ? 'Im z' : 'Im s';

  return (
    <div className="flex w-full flex-col items-center">
      <svg
        width={W}
        height={H}
        className="max-w-full overflow-visible"
        viewBox={`0 0 ${W} ${H}`}
        aria-hidden
      >
        {variant === 's' && (() => {
          const xStableHi = Math.min(0, xMax);
          if (!(xMin < xStableHi)) return null;
          const c1 = mapPoint(xMin, yMin, xMin, xMax, yMin, yMax);
          const c2 = mapPoint(xStableHi, yMin, xMin, xMax, yMin, yMax);
          const c3 = mapPoint(xStableHi, yMax, xMin, xMax, yMin, yMax);
          const c4 = mapPoint(xMin, yMax, xMin, xMax, yMin, yMax);
          return <polygon fill={lhpFill} points={`${c1[0]},${c1[1]} ${c2[0]},${c2[1]} ${c3[0]},${c3[1]} ${c4[0]},${c4[1]}`} />;
        })()}

        <line x1={ox2} y1={oy0} x2={ox1} y2={oy0} stroke={axisStroke} strokeWidth={1.5} />
        <line x1={ox0} y1={oyB} x2={ox0} y2={oyD} stroke={axisStroke} strokeWidth={1.5} />

        {variant === 's' && xMin < 0 && xMax >= 0 && (
          <line
            x1={ox0}
            y1={Math.min(oyB, oyD)}
            x2={ox0}
            y2={Math.max(oyB, oyD)}
            stroke={isDark ? '#fbbf24' : '#d97706'}
            strokeWidth={1.8}
            strokeDasharray="5 4"
          />
        )}

        {/* Osy popisky u směru kladných os */}
        <text
          x={Math.min(ox1 - 4, W - PAD)}
          y={oy0 + 18}
          textAnchor="end"
          fill={axisLabelFill}
          fontSize={12}
          fontWeight={700}
        >
          {reName}
        </text>
        <text
          x={ox0 + 10}
          y={Math.max(oyD - 6, PAD)}
          textAnchor="start"
          fill={axisLabelFill}
          fontSize={12}
          fontWeight={700}
        >
          {imName}
        </text>

        {variant === 'z' && (
          <polyline
            points={circlePolylinePoints(xMin, xMax, yMin, yMax, 1)}
            fill="none"
            stroke={unitStroke}
            strokeWidth={2.8}
            opacity={0.95}
          />
        )}

        {variant === 'z' && showRe1 && (
          <>
            <circle cx={rx1} cy={ry1} r={9} fill="none" stroke={unitStrokeHi} strokeWidth={2.4} />
            <circle cx={rx1} cy={ry1} r={11} fill="none" stroke={unitStroke} strokeWidth={1} opacity={0.5} />
          </>
        )}

        {/* Měřítkové značky ±1 u os */}
        {showRe1 && (
          <line x1={rx1} y1={ry1 - tick} x2={rx1} y2={ry1 + tick} stroke={axisStroke} strokeWidth={1.8} />
        )}
        {showReNeg1 && (
          <line x1={rxN1} y1={ryN1 - tick} x2={rxN1} y2={ryN1 + tick} stroke={axisStroke} strokeWidth={1.8} />
        )}
        {showIm1 && (
          <line x1={ox0 - tick} y1={iy1} x2={ox0 + tick} y2={iy1} stroke={axisStroke} strokeWidth={1.8} />
        )}
        {showImNeg1 && (
          <line x1={ox0 - tick} y1={iyN1} x2={ox0 + tick} y2={iyN1} stroke={axisStroke} strokeWidth={1.8} />
        )}

        {pts.map((p, i) => {
          const [sx, sy] = mapPoint(p.re, p.im, xMin, xMax, yMin, yMax);
          const inside = variant === 'z' ? Math.hypot(p.re, p.im) < 1 - 1e-6 : p.re < -1e-6;
          return (
            <circle key={`${p.re}-${p.im}-${i}`} cx={sx} cy={sy} r={5} fill={inside ? poleIn : poleOut} stroke={isDark ? '#0f172a' : '#fff'} strokeWidth={1} />
          );
        })}

        <text x={ox0 - 16} y={oy0 + 16} textAnchor="middle" fill={numFill} fontSize={13} fontWeight={700}>
          0
        </text>
        {showRe1 && (
          <text x={rx1} y={ry1 + tick + 15} textAnchor="middle" fill={numFill} fontSize={13} fontWeight={700}>
            1
          </text>
        )}
        {showReNeg1 && (
          <text x={rxN1} y={ryN1 + tick + 15} textAnchor="middle" fill={numFill} fontSize={12} fontWeight={600}>
            −1
          </text>
        )}
        {variant === 'z' && showIm1 && (
          <text x={ox0 + tick + 10} y={iy1 + 5} textAnchor="start" fill={numFill} fontSize={13} fontWeight={700}>
            1
          </text>
        )}
        {variant === 'z' && showImNeg1 && (
          <text x={ox0 + tick + 10} y={iyN1 + 5} textAnchor="start" fill={numFill} fontSize={12} fontWeight={600}>
            −1
          </text>
        )}
        {variant === 's' && showIm1 && (
          <text x={ox0 + tick + 10} y={iy1 + 5} textAnchor="start" fill={numFill} fontSize={13} fontWeight={700}>
            1
          </text>
        )}
        {variant === 's' && showImNeg1 && (
          <text x={ox0 + tick + 10} y={iyN1 + 5} textAnchor="start" fill={numFill} fontSize={12} fontWeight={600}>
            −1
          </text>
        )}
      </svg>
      <div
        className={`mt-1 flex gap-3 text-[9px] font-medium uppercase tracking-wide ${
          isDark ? 'text-slate-500' : 'text-slate-600'
        }`}
      >
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: poleIn }} />
          {variant === 'z' ? 'uvnitř |z|=1' : 'Re < 0'}
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: poleOut }} />
          {variant === 'z' ? 'mimo kruh' : 'Re ≥ 0'}
        </span>
      </div>
    </div>
  );
}

export default ComplexPolePlot;
