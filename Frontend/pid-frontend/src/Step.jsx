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
  Filler,
} from 'chart.js';

ChartJS.register(LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function Step({ points }) {
  const pointArray = points?.points || [];
  const aproArray = points?.apro_points || [];

  if (pointArray.length === 0) return null;

  const data = {
    datasets: [
      {
        label: 'Reálná odezva y(t)',
        data: pointArray.map((p) => ({ x: p.t, y: p.y })),
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.12)',
        fill: true,
        tension: 0.24,
        pointRadius: 0,
        borderWidth: 2.5,
      },
      aproArray.length > 0 && {
        label: 'Aproximovaná FOPDT odezva',
        data: aproArray.map((p) => ({ x: p.t, y: p.y })),
        borderColor: '#f59e0b',
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.18,
        pointRadius: 0,
        borderWidth: 2,
        borderDash: [7, 5],
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
          color: '#cbd5e1',
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 18,
          font: { size: 11, weight: '600' },
        },
      },
      title: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: '#334155',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        type: 'linear',
        title: { display: true, text: 'Čas [s]', color: '#94a3b8', font: { size: 11, weight: '600' } },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: '#94a3b8' },
      },
      y: {
        title: { display: true, text: 'Amplituda y(t)', color: '#94a3b8', font: { size: 11, weight: '600' } },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: '#94a3b8' },
      },
    },
  };

  return (
    <div className="h-full min-h-[340px] w-full">
      <Line data={data} options={options} />
    </div>
  );
}

export default Step;
