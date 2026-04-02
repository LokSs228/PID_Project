import React from 'react';
import StabilityPoleChart from './StabilityPoleChart';

function StabilityPanel({ stability, theme, lang = 'cz' }) {
  if (!stability || typeof stability.stable !== 'boolean') return null;

  const isDark = theme === 'dark';
  const isEn = lang === 'en';
  const { stable, simulation_indicates_unstable: simBad, discrete, continuous } = stability;

  const disc = discrete || {};
  const polesZ = disc.poles_z || [];
  const dt = disc.dt;
  const t7Echo = disc.t7;
  const stepsPerSim = disc.steps_per_sim;
  const polesS = continuous?.poles || [];

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

  const thClass = `px-3 py-2 text-left text-[11px] font-bold uppercase tracking-[0.08em] ${
    isDark ? 'text-slate-400' : 'text-slate-600'
  }`;
  const tdClass = `px-3 py-2 font-mono text-xs tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`;
  const sectionTitle = `mb-2 text-[11px] font-bold uppercase tracking-[0.1em] ${isDark ? 'text-slate-500' : 'text-slate-600'}`;

  return (
    <section className={cardClass}>
      <div
        className={`flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3 ${
          isDark ? 'border-slate-700/60 bg-slate-800/60' : 'border-slate-200 bg-slate-50'
        }`}
      >
        <div>
          <h3 className={`text-xs font-semibold uppercase tracking-[0.12em] ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
            {isEn ? 'Closed-loop stability' : 'Stabilita uzavreneho regulacniho obvodu'}
          </h3>
          {dt != null && (
            <p className={`mt-1 text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              {isEn ? 'Discretization step:' : 'Krok diskretizace:'}{' '}
              <span className="font-mono">T = t7 / {stepsPerSim ?? 1500}</span>
              {t7Echo != null && (
                <>
                  {' '}
                  {isEn ? '- current' : '- aktualne'}{' '}
                  <span className="font-mono">
                    t7 = {Number(t7Echo).toFixed(3)} s -&gt; T = {Number(dt).toFixed(6)} s
                  </span>
                </>
              )}
            </p>
          )}
        </div>
        <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wider ${badgeClass}`}>
          {stable
            ? isEn
              ? 'System is stable'
              : 'System je stabilni'
            : isEn
              ? 'System is unstable'
              : 'System je nestabilni'}
        </span>
      </div>

      <div className="space-y-8 p-4">
        {!stable && simBad && (
          <p
            className={`rounded-xl border px-3 py-2 text-[11px] leading-relaxed ${
              isDark ? 'border-amber-500/30 bg-amber-950/35 text-amber-100/90' : 'border-amber-300 bg-amber-50 text-amber-950'
            }`}
          >
            {isEn
              ? 'The discrete linear model predicts stability, but the time simulation shows a non-settling or diverging response (actuator limits, shape of w(t)).'
              : 'Diskretni linearni model predpovida stabilitu, ale casova simulace ukazuje neustaleny nebo divergentni vystup (omezeni akcni veliciny, tvar w(t)).'}
          </p>
        )}

        <div>
          <div className={sectionTitle}>
            {isEn
              ? 'Discrete closed-loop control system - poles in z-plane'
              : 'Diskretni uzavreny regulacni obvod - poly v rovine z'}
          </div>
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2">
            <div className="overflow-x-auto rounded-xl border border-slate-500/10">
              <table className="min-w-full border-collapse text-sm">
                <thead>
                  <tr className={isDark ? 'bg-slate-800/40' : 'bg-slate-100'}>
                    <th className={thClass}>Re(z)</th>
                    <th className={thClass}>Im(z)</th>
                  </tr>
                </thead>
                <tbody className={isDark ? 'divide-y divide-slate-800/80' : 'divide-y divide-slate-200'}>
                  {polesZ.map((p, i) => (
                    <tr key={`${p.re}-${p.im}-${i}`} className={isDark ? 'hover:bg-slate-800/30' : 'hover:bg-slate-50'}>
                      <td className={tdClass}>{Number(p.re).toFixed(6)}</td>
                      <td className={tdClass}>{Number(p.im).toFixed(6)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <StabilityPoleChart variant="z" poles={polesZ} theme={theme} lang={lang} />
          </div>
        </div>

        <div>
          <div className={sectionTitle}>
            {isEn
              ? 'Continuous closed-loop control system - poles in s-plane'
              : 'Spojity uzavreny regulacni obvod - poly v rovine s'}
          </div>
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2">
            <div className="overflow-x-auto rounded-xl border border-slate-500/10">
              <table className="min-w-full border-collapse text-sm">
                <thead>
                  <tr className={isDark ? 'bg-slate-800/40' : 'bg-slate-100'}>
                    <th className={thClass}>Re(s)</th>
                    <th className={thClass}>Im(s)</th>
                  </tr>
                </thead>
                <tbody className={isDark ? 'divide-y divide-slate-800/80' : 'divide-y divide-slate-200'}>
                  {polesS.map((p, i) => (
                    <tr key={`${p.re}-${p.im}-${i}`} className={isDark ? 'hover:bg-slate-800/30' : 'hover:bg-slate-50'}>
                      <td className={tdClass}>{Number(p.re).toFixed(6)}</td>
                      <td className={tdClass}>{Number(p.im).toFixed(6)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <StabilityPoleChart variant="s" poles={polesS} theme={theme} lang={lang} />
          </div>
        </div>
      </div>
    </section>
  );
}

export default StabilityPanel;
