import React from 'react';

function PidTable({ data }) {
  if (!data) return null;

  const regulatorTypes = ['P', 'PI', 'PD', 'PID'];
  const headers = ['Typ', 'Kp', 'Ki', 'Kd'];

  const formatValue = (val) => {
    return (val != null && typeof val === 'number') 
      ? val.toFixed(4) 
      : '–';
  };

  return (
    <div className="overflow-hidden border border-slate-700/50 rounded-2xl bg-slate-900/20 backdrop-blur-md">
      <table className="min-w-full border-collapse text-left text-sm text-slate-300">
        <thead className="bg-slate-800/60 border-b border-slate-700/50">
          <tr>
            {headers.map((head) => (
              <th 
                key={head} 
                className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]"
              >
                {head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {regulatorTypes.map((type) => (
            <tr 
              key={type} 
              className="group hover:bg-blue-500/5 transition-all duration-200"
            >
              <td className="px-6 py-4">
                <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-slate-800 text-blue-400 font-black text-xs border border-slate-700 group-hover:border-blue-500/50 transition-colors">
                  {type}
                </span>
              </td>
              <td className="px-6 py-4 font-mono text-slate-200 tabular-nums">
                {formatValue(data[type]?.Kp)}
              </td>
              <td className="px-6 py-4 font-mono text-slate-400 tabular-nums">
                {formatValue(data[type]?.Ki)}
              </td>
              <td className="px-6 py-4 font-mono text-slate-400 tabular-nums">
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
