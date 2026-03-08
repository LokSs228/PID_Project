import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function Step({ points }) {
  const pointArray = points.points;
  const aproArray = points.apro_points || [];

  if (!pointArray || pointArray.length === 0) return null;

  const data = {
    datasets: [
      {
        label: 'ReГЎlnГЎ odezva y(t)',
        data: pointArray.map(p => ({ x: p.t, y: p.y })),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.08)',
        fill: false,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 3,
      },
      aproArray.length > 0 && {
        label: 'AproximovanГЎ FOPDT yв‚ђ(t)',
        data: aproArray.map(p => ({ x: p.t, y: p.y })),
        borderColor: '#a855f7',
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 2,
        borderDash: [6, 4],
      },
    ].filter(Boolean),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'nearest',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#94a3b8',
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 20,
          font: { size: 11, weight: '600' }
        },
      },
      title: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: '#334155',
        borderWidth: 1,
      }
    },
    scales: {
      x: {
        type: 'linear',
        title: { display: true, text: 'ДЊas [s]', color: '#64748b', font: { size: 11, weight: 'bold' } },
        grid: { color: '#1e293b', drawBorder: false },
        ticks: { color: '#64748b' },
      },
      y: {
        title: { display: true, text: 'Amplituda y(t)', color: '#64748b', font: { size: 11, weight: 'bold' } },
        grid: { color: '#1e293b', drawBorder: false },
        ticks: { color: '#64748b' },
      },
    },
  };

  return (
    <div className="w-full h-full min-h-[350px]">
      <Line data={data} options={options} />
    </div>
  );
}

export default Step;
