import React from 'react';

function MetricsTable({ metrics, theme, lang = 'cz' }) {
  if (!metrics) return null;
  const isDark = theme === 'dark';
  const isEn = lang === 'en';

  const { overshoot, settlingTime, settlingStatus, IAE, ITAE } = metrics;

  const rows = [
    { key: 'overshoot', label: isEn ? 'Overshoot 5% [%]' : 'Prekmit 5% [%]', value: overshoot },
    { key: 'settling', label: isEn ? 'Settling time [s]' : 'Doba ustaleni [s]', value: settlingTime },
    { key: 'iae', label: 'IAE [s]', value: IAE },
    { key: 'itae', label: isEn ? 'ITAE [s^2]' : 'ITAE [s^2]', value: ITAE },
  ];

  const formatRowValue = (row) => {
    if (row.key === 'settling' && settlingStatus === 'unstable_or_not_settled') {
      return isEn ? 'System is unstable / not settled' : 'System je nestabilni / neustaleny';
    }
    if (row.value === undefined || row.value === null) {
      return '-';
    }
    return Number(row.value).toFixed(4);
  };

  return (
    <div
      className={`overflow-x-auto rounded-2xl ${
        isDark ? 'border border-slate-700/60 bg-slate-900/50' : 'border border-slate-200 bg-white'
      }`}
    >
      <div
        className={`border-b px-4 py-3 ${isDark ? 'border-slate-700/60 bg-slate-800/70' : 'border-slate-200 bg-slate-100'}`}
      >
        <h3 className={`text-sm font-semibold uppercase tracking-[0.1em] ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
          {isEn ? 'Final metrics' : 'Vysledne metriky'}
        </h3>
      </div>

      <table className="min-w-full border-collapse text-[15px]">
        <thead>
          <tr className={`text-left text-xs uppercase tracking-[0.08em] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            <th className="px-4 py-2.5 font-semibold">{isEn ? 'Metric' : 'Metrika'}</th>
            <th className="px-4 py-2.5 font-semibold">{isEn ? 'Value' : 'Hodnota'}</th>
          </tr>
        </thead>
        <tbody className={isDark ? 'divide-y divide-slate-800/80' : 'divide-y divide-slate-200'}>
          {rows.map((row) => (
            <tr key={row.key} className={`transition ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`}>
              <td className={`px-4 py-3 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{row.label}</td>
              <td className={`px-4 py-3 font-mono tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                {formatRowValue(row)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default MetricsTable;
