import React from 'react';

function PidTable({ data }) {
  if (!data) return null;

  const regulatorTypes = ['P', 'PI', 'PD', 'PID'];
  const headers = ['Typ regulátoru', 'Kp', 'Ki', 'Kd'];

  const formatValue = (val) => (val != null && typeof val === 'number' ? val.toFixed(4) : '—');

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
      <table className="min-w-full border-collapse text-left text-sm text-slate-700">
        <thead className="border-b border-slate-200 bg-slate-100">
          <tr>
            {headers.map((head) => (
              <th key={head} className="px-5 py-3 text-[10px] font-bold uppercase tracking-[0.15em] text-slate-600">
                {head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {regulatorTypes.map((type) => (
            <tr key={type} className="transition hover:bg-slate-50">
              <td className="px-5 py-3">
                <span className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-slate-100 px-2.5 py-1 text-xs font-semibold text-sky-700">
                  {type}
                </span>
              </td>
              <td className="px-5 py-3 font-mono tabular-nums text-slate-900">{formatValue(data[type]?.Kp)}</td>
              <td className="px-5 py-3 font-mono tabular-nums text-slate-700">{formatValue(data[type]?.Ki)}</td>
              <td className="px-5 py-3 font-mono tabular-nums text-slate-700">{formatValue(data[type]?.Kd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PidTable;
