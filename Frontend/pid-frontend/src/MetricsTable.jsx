import React from 'react';

function MetricsTable({ metrics }) {
  if (!metrics) return null;

  // ИСПРАВЛЕНИЕ: изменили settling_time на settlingTime
  // (или убедитесь, что имя здесь совпадает с тем, что вы задали в App.js)
  const { overshoot, settlingTime, IAE, ITAE } = metrics;

  return (
    <div style={{ marginTop: 20 }}>
      <h3>Výsledné metriky simulace</h3>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #ccc', padding: 8 }}>Metrika</th>
            <th style={{ border: '1px solid #ccc', padding: 8 }}>Hodnota</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>Overshoot (%)</td>
            {/* Можно добавить .toFixed(2) для красивого отображения чисел */}
            <td style={{ border: '1px solid #ccc', padding: 8 }}>
              {overshoot !== undefined ? Number(overshoot).toFixed(2) : '-'}
            </td>
          </tr>
          <tr>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>Settling Time</td>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>
              {settlingTime !== undefined ? Number(settlingTime).toFixed(4) : '-'}
            </td>
          </tr>
          <tr>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>IAE</td>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>
              {IAE !== undefined ? Number(IAE).toFixed(4) : '-'}
            </td>
          </tr>
          <tr>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>ITAE</td>
            <td style={{ border: '1px solid #ccc', padding: 8 }}>
              {ITAE !== undefined ? Number(ITAE).toFixed(4) : '-'}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default MetricsTable;