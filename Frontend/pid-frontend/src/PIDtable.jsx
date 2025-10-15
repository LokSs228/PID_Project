import React from 'react';

function PidTable({ data }) {
  if (!data) return null;

  const regulatorTypes = ['P', 'PI', 'PID'];
  const headers = ['Typ regulátoru', 'Kp', 'Ki', 'Kd'];

  return (
    <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', marginTop: 20 }}>
      <thead>
        <tr>
          {headers.map((head) => (
            <th key={head}>{head}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {regulatorTypes.map((type) => (
          <tr key={type}>
            <td>{type}</td>
            <td>{data[type]?.Kp?.toFixed(3) ?? '–'}</td>
            <td>{data[type]?.Ki?.toFixed(3) ?? '–'}</td>
            <td>{data[type]?.Kd?.toFixed(3) ?? '–'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default PidTable;
