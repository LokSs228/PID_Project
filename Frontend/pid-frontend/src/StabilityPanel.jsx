import React from 'react';

function StabilityPanel({ stability, theme }) {
  if (!stability || typeof stability.stable !== 'boolean') return null;

  const isDark = theme === 'dark';
  const { stable, poles, continuous_poles_stable: contOk, simulation_indicates_unstable: simBad } = stability;

  const cardClass = `rounded-2xl border overflow-hidden ${
    isDark ? 'border-slate-700/60 bg-slate-900/50' : 'border-slate-200 bg-white'
  }`;

  const badgeClass = stable
    ? isDark
      ? 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/40'
      : 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200'
    : isDark
      ? 'bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/40'
      : 'bg-rose-50 text-rose-800 ring-1 ring-rose-200';

  const thClass = `px-3 py-2 text-left text-[10px] font-bold uppercase tracking-[0.1em] ${
    isDark ? 'text-slate-400' : 'text-slate-600'
  }`;
  const tdClass = `px-3 py-2 font-mono text-xs tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`;

  const skipSim = contOk === false;

  return (
    <section className={cardClass}>
      <div
        className={`flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3 ${
          isDark ? 'border-slate-700/60 bg-slate-800/60' : 'border-slate-200 bg-slate-50'
        }`}
      >
        <h3 className={`text-xs font-semibold uppercase tracking-[0.12em] ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
          Stabilita uzavřené smyčky
        </h3>
        <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wider ${badgeClass}`}>
          {stable ? 'Systém je stabilní' : 'Systém je nestabilní'}
        </span>
      </div>

      <div className="p-4">
        {!stable && simBad && (
          <p
            className={`mb-4 rounded-xl border px-3 py-2 text-[11px] leading-relaxed ${
              isDark ? 'border-amber-500/30 bg-amber-950/35 text-amber-100/90' : 'border-amber-300 bg-amber-50 text-amber-950'
            }`}
          >
            Spojitý model má póly v levé polovině roviny, ale diskretní simulace (PID v čase) ukazuje neustálený nebo
            divergentní chování — jako závěr se bere simulace.
          </p>
        )}
        {!stable && skipSim && (
          <p
            className={`mb-4 rounded-xl border px-3 py-2 text-[11px] leading-relaxed ${
              isDark ? 'border-rose-500/25 bg-rose-950/40 text-rose-200/90' : 'border-rose-200 bg-rose-50 text-rose-900'
            }`}
          >
            Simulace regulačního pochodu a tabulka metrik kvality nejsou zobrazeny.
          </p>
        )}

        <div className="overflow-x-auto rounded-xl border border-slate-500/10">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className={isDark ? 'bg-slate-800/40' : 'bg-slate-100'}>
                <th className={thClass}>Re(p)</th>
                <th className={thClass}>Im(p)</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'divide-y divide-slate-800/80' : 'divide-y divide-slate-200'}>
              {(poles || []).map((p, i) => (
                <tr key={`${p.re}-${p.im}-${i}`} className={isDark ? 'hover:bg-slate-800/30' : 'hover:bg-slate-50'}>
                  <td className={tdClass}>{Number(p.re).toFixed(6)}</td>
                  <td className={tdClass}>{Number(p.im).toFixed(6)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export default StabilityPanel;
