import React from 'react';
import {
  Chart as ChartJS,
  LinearScale,
  CategoryScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(LinearScale, CategoryScale, PointElement, LineElement, Title, Tooltip, Legend);

function Sim({ sim_points, y0 }) {
  if (!sim_points || sim_points.length === 0) return null;

  const wData = sim_points.map(point => ({ x: Number(point.t), y: Number(point.w) }));
  const yData = sim_points.map(point => ({ x: Number(point.t), y: Number(point.y) }));
  const uData = sim_points.map(point => ({ x: Number(point.t), y: Number(point.u) }));

  const data = {
    datasets: [
      {
        label: 'Požadovaná hodnota (w)',
        data: wData,
        borderColor: '#94a3b8', // slate-400
        borderDash: [5, 5],
        borderWidth: 2,
        pointRadius: 0,
      },
      {
        label: 'Výstup systému (y)',
        data: yData,
        borderColor: '#3b82f6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'Řídicí vstup (u)',
        data: uData,
        borderColor: '#10b981', // emerald-500
        borderWidth: 1.5,
        pointRadius: 0,
        yAxisID: 'y1',
      },
      {
        label: 'Počáteční bod (y₀)',
        data: [{ x: Number(sim_points[0].t), y: Number(y0) }],
        borderColor: '#ef4444', // red-500
        backgroundColor: '#ef4444',
        pointRadius: 6,
        showLine: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false, 
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#cbd5e1', // slate-300
          usePointStyle: true,
          font: { size: 12, weight: '600' }
        },
      },
      title: { display: false },
      tooltip: {
        backgroundColor: '#1e293b', // slate-800
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: '#334155',
        borderWidth: 1,
        padding: 12,
        boxPadding: 6,
      },
    },
    scales: {
      x: {
        type: 'linear',
        title: { display: true, text: 'Čas (s)', color: '#64748b' },
        grid: { color: '#334155', drawBorder: false }, // slate-700
        ticks: { color: '#64748b' },
      },
      y: {
        type: 'linear',
        position: 'left',
        title: { display: true, text: 'Hodnota (w a y)', color: '#3b82f6' },
        grid: { color: '#334155', drawBorder: false },
        ticks: { color: '#94a3b8' },
      },
      y1: {
        type: 'linear',
        position: 'right',
        title: { display: true, text: 'Řídicí vstup (u)', color: '#10b981' },
        grid: { drawOnChartArea: false },
        ticks: { color: '#10b981' },
      },
    },
  };

  return (
    <div className="w-full h-full min-h-[400px]">
      <Line data={data} options={options} />
    </div>
  );
}

export default Sim;

