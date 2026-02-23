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
  const inflection = points.inflection;
  const tangent = points.tangent_line;
  const A_L = points.A_L_points;
  const aproArray = points.apro_points || [];

  if (!pointArray || pointArray.length === 0) return null;

  // Рассчитаем данные для отрисовки касательной
  let tangentData = [];
  if (inflection && tangent) {
    const tMax = pointArray[pointArray.length - 1].t;
    const tMin = 0;
    const tEnd = inflection.t + (tMax - inflection.t) * 0.5;

    const yMin = tangent.slope * (tMin - inflection.t) + inflection.y;
    const yMax = tangent.slope * (tEnd - inflection.t) + inflection.y;

    tangentData = [
      { x: tMin, y: yMin },
      { x: tEnd, y: yMax }
    ];
  }

  const data = {
    datasets: [
      // 1. Главная кривая (реальная система)
      {
        label: 'Reálná odezva y(t)',
        data: pointArray.map(p => ({ x: p.t, y: p.y })),
        borderColor: '#3b82f6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.08)',
        fill: false,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 3,
      },
      // 2. Аппроксимация FOPDT (модель)
      aproArray.length > 0 && {
        label: 'Aproximovaná FOPDT yₐ(t)',
        data: aproArray.map(p => ({ x: p.t, y: p.y })),
        borderColor: '#a855f7', // purple-500
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 2,
        borderDash: [6, 4], // Средний пунктир
      },
      // 3. Вспомогательная линия (касательная)
      tangentData.length > 0 && {
        label: 'Inflexní tečna',
        data: tangentData,
        borderColor: 'rgba(239, 68, 68, 0.6)', // red-500 полупрозрачный
        borderWidth: 1.5,
        borderDash: [3, 3], // Мелкий пунктир
        fill: false,
        pointRadius: 0,
        tension: 0,
      },
      // 4. Аналитические точки
      inflection && {
        label: 'Inflexní bod',
        data: [{ x: inflection.t, y: inflection.y }],
        pointRadius: 5,
        pointBackgroundColor: '#ef4444', // red-500
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        showLine: false,
      },
      A_L && {
        label: 'Bod A (osa y)',
        data: [{ x: 0, y: A_L.A }],
        pointRadius: 5,
        pointBackgroundColor: '#10b981', // emerald-500
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        showLine: false,
      },
      A_L && {
        label: 'Bod L (zpoždění)',
        data: [{ x: A_L.L, y: 0 }],
        pointRadius: 5,
        pointBackgroundColor: '#f59e0b', // amber-500
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        showLine: false,
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
          color: '#94a3b8', // slate-400
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
        title: { display: true, text: 'Čas [s]', color: '#64748b', font: { size: 11, weight: 'bold' } },
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