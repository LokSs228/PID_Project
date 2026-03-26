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

  const wData = sim_points.map((point) => ({ x: Number(point.t), y: Number(point.w) }));
  const yData = sim_points.map((point) => ({ x: Number(point.t), y: Number(point.y) }));
  const uData = sim_points.map((point) => ({ x: Number(point.t), y: Number(point.u) }));

  const data = {
    datasets: [
      {
        label: 'Požadovaná hodnota (w)',
        data: wData,
        borderColor: '#94a3b8',
        borderDash: [5, 5],
        borderWidth: 2,
        pointRadius: 0,
      },
      {
        label: 'Výstup systému (y)',
        data: yData,
        borderColor: '#22d3ee',
        backgroundColor: 'rgba(34, 211, 238, 0.12)',
        fill: true,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.12,
      },
      {
        label: 'Řídicí vstup (u)',
        data: uData,
        borderColor: '#34d399',
        borderWidth: 1.6,
        pointRadius: 0,
        yAxisID: 'y1',
      },
      {
        label: 'Počáteční bod (y₀)',
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
    layout: {
      padding: { top: 6, right: 10, bottom: 2, left: 4 },
    },
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#cbd5e1',
          usePointStyle: true,
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
        grace: '2%',
        title: { display: true, text: 'Čas [s]', color: '#94a3b8' },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: '#94a3b8', maxTicksLimit: 8 },
      },
      y: {
        type: 'linear',
        position: 'left',
        grace: '6%',
        title: { display: true, text: 'Hodnota (w, y)', color: '#38bdf8' },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: '#94a3b8', maxTicksLimit: 7 },
      },
      y1: {
        type: 'linear',
        position: 'right',
        grace: '8%',
        title: { display: true, text: 'Řídicí vstup (u)', color: '#34d399' },
        grid: { drawOnChartArea: false },
        ticks: { color: '#34d399', maxTicksLimit: 7 },
      },
    },
  };

  return (
    <div className="h-full w-full overflow-hidden">
      <Line data={data} options={options} />
    </div>
  );
}

export default Sim;
