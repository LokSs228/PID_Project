import React from 'react';

function MetricsTable({ metrics }) {
  if (!metrics) return null;

  const { overshoot, settlingTime, settlingStatus, IAE, ITAE } = metrics;

  const rows = [
    { label: 'Prekmit', value: overshoot, unit: '%' },
    { label: 'Doba ustaleni (5%)', value: settlingTime, unit: 's' },
    { label: 'IAE', value: IAE, unit: 's' },
    { label: 'ITAE', value: ITAE, unit: 's^2' },
  ];

  const formatRowValue = (row) => {
    if (row.label === 'Doba ustaleni (5%)' && settlingStatus === 'unstable_or_not_settled') {
      return 'System je nestabilni / neustaleny';
    }
    if (row.value === undefined || row.value === null) {
      return '-';
    }
    return `${Number(row.value).toFixed(4)} ${row.unit}`;
  };

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
      <div className="border-b border-slate-200 bg-slate-100 px-4 py-3">
        <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-700">Vysledne metriky</h3>
      </div>

      <table className="min-w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-[0.1em] text-slate-600">
            <th className="px-4 py-2.5 font-semibold">Metrika</th>
            <th className="px-4 py-2.5 font-semibold">Hodnota</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {rows.map((row) => (
            <tr key={row.label} className="transition hover:bg-slate-50">
              <td className="px-4 py-3 text-slate-800">{row.label}</td>
              <td className="px-4 py-3 font-mono tabular-nums text-slate-900">{formatRowValue(row)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default MetricsTable;
