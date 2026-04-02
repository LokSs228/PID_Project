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

function Sim({ sim_points, y0, theme, lang = 'cz' }) {
  const isDark = theme === 'dark';
  const isEn = lang === 'en';
  if (!sim_points || sim_points.length === 0) return null;

  const wData = sim_points.map((point) => ({ x: Number(point.t), y: Number(point.w) }));
  const yData = sim_points.map((point) => ({ x: Number(point.t), y: Number(point.y) }));
  const uData = sim_points.map((point) => ({ x: Number(point.t), y: Number(point.u) }));

  const data = {
    datasets: [
      {
        label: isEn ? 'Setpoint (w)' : 'Pozadovana hodnota (w)',
        data: wData,
        borderColor: '#94a3b8',
        borderDash: [5, 5],
        borderWidth: 2,
        pointRadius: 0,
      },
      {
        label: isEn ? 'Plant output (y)' : 'Vystup systemu (y)',
        data: yData,
        borderColor: '#22d3ee',
        backgroundColor: 'rgba(34, 211, 238, 0.12)',
        fill: true,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.12,
      },
      {
        label: isEn ? 'Control input (u)' : 'Ridici vstup (u)',
        data: uData,
        borderColor: '#34d399',
        borderWidth: 1.6,
        pointRadius: 0,
        yAxisID: 'y1',
      },
      {
        label: isEn ? 'Initial point (y0)' : 'Pocatecni bod (y0)',
        data: [{ x: Number(sim_points[0].t), y: Number(y0) }],
        borderColor: '#f43f5e',
        backgroundColor: '#f43f5e',
        pointRadius: 5,
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
          color: isDark ? '#cbd5e1' : '#334155',
          usePointStyle: true,
          font: { size: 12, weight: '600' },
        },
      },
      title: { display: false },
      tooltip: {
        backgroundColor: isDark ? '#0f172a' : '#ffffff',
        titleColor: isDark ? '#f8fafc' : '#0f172a',
        bodyColor: isDark ? '#cbd5e1' : '#334155',
        borderColor: isDark ? '#334155' : '#cbd5e1',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        type: 'linear',
        title: { display: true, text: isEn ? 'Time [s]' : 'Cas [s]', color: isDark ? '#94a3b8' : '#475569' },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: isDark ? '#94a3b8' : '#64748b' },
      },
      y: {
        type: 'linear',
        position: 'left',
        title: { display: true, text: isEn ? 'Value [w, y]' : 'Hodnota [w, y]', color: '#38bdf8' },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: isDark ? '#94a3b8' : '#64748b' },
      },
      y1: {
        type: 'linear',
        position: 'right',
        title: { display: true, text: isEn ? 'Control input (u)' : 'Ridici vstup (u)', color: '#34d399' },
        grid: { drawOnChartArea: false },
        ticks: { color: '#34d399' },
      },
    },
  };

  return (
    <div className="h-full min-h-[420px] w-full">
      <Line data={data} options={options} />
    </div>
  );
}

export default Sim;
