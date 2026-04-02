import React from 'react';

function PidTable({ data, theme, lang = 'cz' }) {
  if (!data) return null;
  const isDark = theme === 'dark';
  const isEn = lang === 'en';

  const regulatorTypes = ['P', 'PI', 'PD', 'PID'];
  const headers = [isEn ? 'Controller' : 'Typ regulatoru', 'Kp', 'Ki', 'Kd'];

  const formatValue = (val) => (val != null && typeof val === 'number' ? val.toFixed(4) : '-');

  return (
    <div
      className={`overflow-x-auto rounded-2xl ${
        isDark ? 'border border-slate-700/60 bg-slate-900/50' : 'border border-slate-200 bg-white'
      }`}
    >
      <table className={`min-w-full border-collapse text-left text-sm ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
        <thead className={isDark ? 'border-b border-slate-700/60 bg-slate-800/70' : 'border-b border-slate-200 bg-slate-100'}>
          <tr>
            {headers.map((head) => (
              <th
                key={head}
                className={`px-5 py-3 text-[10px] font-bold uppercase tracking-[0.15em] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}
              >
                {head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={isDark ? 'divide-y divide-slate-800/80' : 'divide-y divide-slate-200'}>
          {regulatorTypes.map((type) => (
            <tr key={type} className={`transition ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`}>
              <td className="px-5 py-3">
                <span
                  className={`inline-flex items-center justify-center rounded-md px-2.5 py-1 text-xs font-semibold ${
                    isDark
                      ? 'border border-slate-600 bg-slate-800 text-sky-300'
                      : 'border border-slate-300 bg-slate-100 text-sky-700'
                  }`}
                >
                  {type}
                </span>
              </td>
              <td className={`px-5 py-3 font-mono tabular-nums ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                {formatValue(data[type]?.Kp)}
              </td>
              <td className={`px-5 py-3 font-mono tabular-nums ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                {formatValue(data[type]?.Ki)}
              </td>
              <td className={`px-5 py-3 font-mono tabular-nums ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                {formatValue(data[type]?.Kd)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PidTable;
