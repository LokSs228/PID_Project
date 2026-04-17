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

function Step({ points, approxModel, theme, lang = 'cz' }) {
  const isDark = theme === 'dark';
  const isEn = lang === 'en';
  const pointArray = points?.points || [];
  const aproArray = points?.apro_points || [];
  const k = Number(approxModel?.K);
  const t = Number(approxModel?.T);
  const l = Number(approxModel?.L);
  const showApproxParams = Number.isFinite(k) && Number.isFinite(t) && Number.isFinite(l) && t > 0;

  const formatParam = (val) => (Number.isFinite(val) ? val.toFixed(4) : '-');

  if (pointArray.length === 0) return null;

  const data = {
    datasets: [
      {
        label: isEn ? 'Measured response y(t)' : 'Reálná odezva y(t)',
        data: pointArray.map((p) => ({ x: p.t, y: p.y })),
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.12)',
        fill: true,
        tension: 0.24,
        pointRadius: 0,
        borderWidth: 2.5,
      },
      aproArray.length > 0 && {
        label: isEn ? 'FOPDT approximation' : 'Aproximovaná FOPDT odezva',
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
          color: isDark ? '#cbd5e1' : '#334155',
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 18,
          font: { size: 11, weight: '600' },
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
        title: {
          display: true,
          text: isEn ? 'Time [s]' : 'Čas [s]',
          color: isDark ? '#94a3b8' : '#475569',
          font: { size: 11, weight: '600' },
        },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: isDark ? '#94a3b8' : '#64748b' },
      },
      y: {
        title: {
          display: true,
          text: isEn ? 'Amplitude y(t)' : 'Amplituda y(t)',
          color: isDark ? '#94a3b8' : '#475569',
          font: { size: 11, weight: '600' },
        },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: isDark ? '#94a3b8' : '#64748b' },
      },
    },
  };

  return (
    <div className="h-full min-h-[340px] w-full overflow-hidden">
      {showApproxParams && (
        <div className="mb-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
          <div
            className={`mb-2 text-[10px] font-bold uppercase tracking-[0.14em] ${isDark ? 'text-amber-300' : 'text-amber-700'}`}
          >
            {isEn ? 'Approximated FOPDT model' : 'Aproximovaný FOPDT model'}
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div
              className={`rounded-md border p-2 text-center ${
                isDark ? 'border-amber-400/30 bg-slate-900/60 text-slate-200' : 'border-amber-300 bg-white text-slate-800'
              }`}
            >
              K = <span className={`font-mono ${isDark ? 'text-amber-200' : 'text-amber-700'}`}>{formatParam(k)}</span>
            </div>
            <div
              className={`rounded-md border p-2 text-center ${
                isDark ? 'border-amber-400/30 bg-slate-900/60 text-slate-200' : 'border-amber-300 bg-white text-slate-800'
              }`}
            >
              T = <span className={`font-mono ${isDark ? 'text-amber-200' : 'text-amber-700'}`}>{formatParam(t)}</span>
            </div>
            <div
              className={`rounded-md border p-2 text-center ${
                isDark ? 'border-amber-400/30 bg-slate-900/60 text-slate-200' : 'border-amber-300 bg-white text-slate-800'
              }`}
            >
              L = <span className={`font-mono ${isDark ? 'text-amber-200' : 'text-amber-700'}`}>{formatParam(l)}</span>
            </div>
          </div>
        </div>
      )}
      <Line data={data} options={options} />
    </div>
  );
}

export default Step;
