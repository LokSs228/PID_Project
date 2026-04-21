import React from 'react';

function MetricsTable({ metrics, theme, lang = 'cz' }) {
  if (!metrics) return null;
  const isDark = theme === 'dark';
  const isEn = lang === 'en';

  const { overshoot, settlingTime, settlingStatus, IAE, ITAE, stabilityMargins } = metrics;

  const metricRows = [
    { key: 'overshoot', label: isEn ? 'Overshoot 5% [%]' : 'Relativní překmit [%]', value: overshoot },
    { key: 'settling', label: isEn ? 'Settling time [s]' : 'Doba ustálení 5 % [s]', value: settlingTime },
    { key: 'iae', label: 'IAE [s]', value: IAE },
    { key: 'itae', label: 'ITAE [s^2]', value: ITAE },
  ];

  const marginRows = [
    {
      key: 'gain_margin',
      label: isEn ? 'Gain margin [dB]' : 'Zesilovací rezerva [dB]',
      value: stabilityMargins?.gain_margin_db,
      infinite: !!stabilityMargins?.gain_margin_infinite,
    },
    {
      key: 'phase_margin',
      label: isEn ? 'Phase margin [deg]' : 'Fázová rezerva [deg]',
      value: stabilityMargins?.phase_margin_deg,
      infinite: !!stabilityMargins?.phase_margin_infinite,
    },
  ];

  const formatMetricValue = (row) => {
    if (row.key === 'settling' && settlingStatus === 'unstable_or_not_settled') {
      return isEn ? 'System is unstable / not settled' : 'Systém je nestabilní / neustálený';
    }
    if (row.value === undefined || row.value === null) return '-';
    return Number(row.value).toFixed(4);
  };

  const formatMarginValue = (row) => {
    if (row.infinite) return '∞';
    if (row.value === undefined || row.value === null) return isEn ? 'Not available' : 'Nedostupné';
    return Number(row.value).toFixed(4);
  };

  const cardClass = isDark
    ? 'overflow-visible rounded-2xl border border-slate-700/60 bg-slate-900/50'
    : 'overflow-visible rounded-2xl border border-slate-200 bg-white';

  const headerClass = isDark
    ? 'border-b border-slate-700/60 bg-slate-800/70'
    : 'border-b border-slate-200 bg-slate-100';

  const rowDividerClass = isDark ? 'divide-y divide-slate-800/80' : 'divide-y divide-slate-200';

  const qualityGuide = isEn
    ? [
        'Overshoot [%]: how much the output exceeds the setpoint after a step.',
        'Settling time 5% [s]: time after which the output remains in the 5% tolerance band around the target.',
        'IAE and ITAE describe total control error. Lower values indicate better tuning.',
      ]
    : [
        'Relativní překmit [%]: jak moc výstup překročí požadovanou hodnotu po skoku.',
        'Doba ustálení 5 % [s]: čas, za který výstup zůstane v tolerančním pásmu kolem cíle.',
        'IAE a ITAE charakterizují celkovou regulační chybu. Čím nižší hodnota, tím kvalitnější nastavení.',
      ];

  const marginGuide = isEn
    ? [
        'Gain margin [dB]: how much loop gain can increase before reaching the stability limit; higher positive values mean higher robustness.',
        'Phase margin [deg]: phase distance from the critical point (-180 deg) at gain crossover; higher values usually mean less tendency to oscillate.',
      ]
    : [
        'Zesilovací rezerva [dB]: o kolik může vzrůst zesílení smyčky, než dosáhne hranice nestability; vyšší kladná hodnota znamená vyšší robustnost.',
        'Fázová rezerva [deg]: fázová vzdálenost od kritického bodu (-180 deg) při frekvenci přechodu zesílení; vyšší hodnota obvykle znamená menší sklon ke kmitání.',
      ];

  const infoBtnClass = isDark
    ? 'flex h-6 w-6 items-center justify-center rounded-full border border-sky-400/70 bg-sky-500/20 text-[11px] font-black text-sky-200 shadow-sm shadow-sky-900/40 transition-colors hover:bg-sky-500/35 hover:text-white focus:border-sky-300 focus:bg-sky-500/35 focus:text-white focus:outline-none'
    : 'flex h-6 w-6 items-center justify-center rounded-full border border-sky-500/70 bg-sky-100 text-[11px] font-black text-sky-700 shadow-sm shadow-sky-200 transition-colors hover:bg-sky-200 hover:text-sky-900 focus:border-sky-500 focus:bg-sky-200 focus:text-sky-900 focus:outline-none';

  const popoverClass = isDark
    ? 'invisible absolute right-0 top-7 z-[120] w-[min(30rem,calc(100vw-2rem))] rounded-xl border border-sky-500/40 bg-slate-800 p-4 text-[12px] leading-relaxed text-slate-200 opacity-0 shadow-2xl shadow-black/50 transition-all duration-200 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100'
    : 'invisible absolute right-0 top-7 z-[120] w-[min(30rem,calc(100vw-2rem))] rounded-xl border border-sky-300 bg-white p-4 text-[12px] leading-relaxed text-slate-800 opacity-0 shadow-2xl shadow-slate-300/70 transition-all duration-200 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100';

  return (
    <div className="space-y-4">
      <div className={cardClass}>
        <div className={`px-4 py-3 ${headerClass}`}>
          <div className="flex items-center gap-2">
            <h3 className={`text-sm font-semibold uppercase tracking-[0.1em] ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
              {isEn ? 'Final metrics' : 'Výsledné metriky'}
            </h3>
            <div className="group relative">
              <button type="button" aria-label={isEn ? 'Quality metrics info' : 'Informace o metrikách kvality'} className={infoBtnClass}>
                i
              </button>
              <div className={popoverClass}>
                <p>{qualityGuide[0]}</p>
                <p className="mt-2">{qualityGuide[1]}</p>
                <p className="mt-2">{qualityGuide[2]}</p>
              </div>
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-[15px]">
            <thead>
              <tr className={`text-left text-xs uppercase tracking-[0.08em] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                <th className="px-4 py-2.5 font-semibold">{isEn ? 'Metric' : 'Metrika'}</th>
                <th className="px-4 py-2.5 font-semibold">{isEn ? 'Value' : 'Hodnota'}</th>
              </tr>
            </thead>
            <tbody className={rowDividerClass}>
              {metricRows.map((row) => (
                <tr key={row.key} className={`transition ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`}>
                  <td className={`px-4 py-3 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{row.label}</td>
                  <td className={`px-4 py-3 font-mono tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    {formatMetricValue(row)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={cardClass}>
        <div className={`px-4 py-3 ${headerClass}`}>
          <div className="flex items-center gap-2">
            <h3 className={`text-sm font-semibold uppercase tracking-[0.1em] ${isDark ? 'text-amber-300' : 'text-amber-700'}`}>
              {isEn ? 'Stability margins' : 'Rezervy stability'}
            </h3>
            <div className="group relative">
              <button type="button" aria-label={isEn ? 'Stability margins info' : 'Informace o rezervách stability'} className={infoBtnClass}>
                i
              </button>
              <div className={popoverClass}>
                <p>{marginGuide[0]}</p>
                <p className="mt-2">{marginGuide[1]}</p>
              </div>
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-[15px]">
            <thead>
              <tr className={`text-left text-xs uppercase tracking-[0.08em] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                <th className="px-4 py-2.5 font-semibold">{isEn ? 'Margin' : 'Rezerva'}</th>
                <th className="px-4 py-2.5 font-semibold">{isEn ? 'Value' : 'Hodnota'}</th>
              </tr>
            </thead>
            <tbody className={rowDividerClass}>
              {marginRows.map((row) => (
                <tr key={row.key} className={`transition ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`}>
                  <td className={`px-4 py-3 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{row.label}</td>
                  <td className={`px-4 py-3 font-mono tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    {formatMarginValue(row)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default MetricsTable;
