import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  ScatterController,
} from 'chart.js';
import { Scatter } from 'react-chartjs-2';

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend, ScatterController);

const CIRCLE_SEG = 144;

function unitCirclePoints() {
  const pts = [];
  for (let i = 0; i <= CIRCLE_SEG; i++) {
    const t = (i / CIRCLE_SEG) * Math.PI * 2;
    pts.push({ x: Math.cos(t), y: Math.sin(t) });
  }
  return pts;
}

function boundsZ(poles) {
  let maxR = 1;
  for (const p of poles) {
    maxR = Math.max(maxR, Math.hypot(Number(p.re), Number(p.im)));
  }
  const L = Math.max(1.15, maxR * 1.12);
  return { xMin: -L, xMax: L, yMin: -L, yMax: L };
}

function boundsS(poles) {
  if (!poles.length) {
    return { xMin: -2, xMax: 0.6, yMin: -1.6, yMax: 1.6 };
  }
  let minRe = Infinity;
  let maxRe = -Infinity;
  let minIm = Infinity;
  let maxIm = -Infinity;
  for (const p of poles) {
    const re = Number(p.re);
    const im = Number(p.im);
    minRe = Math.min(minRe, re);
    maxRe = Math.max(maxRe, re);
    minIm = Math.min(minIm, im);
    maxIm = Math.max(maxIm, im);
  }
  const span = Math.max(Math.abs(minRe), Math.abs(maxRe), Math.abs(minIm), Math.abs(maxIm), 0.4);
  const pad = span * 0.14 + 0.06;
  return {
    xMin: Math.min(minRe - pad, -pad * 0.5),
    xMax: Math.max(maxRe + pad, pad * 0.5),
    yMin: minIm - pad,
    yMax: maxIm + pad,
  };
}

/**
 * variant "z" — |z|=1 (čárkovaně), póly |z|<1 / |z|≥1
 * variant "s" — čára Re=0 (čárkovaně), póly Re<0 / Re≥0
 */
function StabilityPoleChart({ variant, poles, theme }) {
  const isDark = theme === 'dark';

  const { data, xMin, xMax, yMin, yMax } = useMemo(() => {
    const norm = (poles || []).map((p) => ({ re: Number(p.re), im: Number(p.im) }));

    if (variant === 'z') {
      const b = boundsZ(norm);
      const inside = norm.filter((p) => Math.hypot(p.re, p.im) < 1 - 1e-9);
      const outside = norm.filter((p) => Math.hypot(p.re, p.im) >= 1 - 1e-9);
      return {
        xMin: b.xMin,
        xMax: b.xMax,
        yMin: b.yMin,
        yMax: b.yMax,
        data: {
          datasets: [
            {
              label: '|z| = 1',
              data: unitCirclePoints(),
              showLine: true,
              pointRadius: 0,
              pointHoverRadius: 0,
              borderColor: isDark ? '#38bdf8' : '#0284c7',
              borderWidth: 2,
              borderDash: [7, 5],
              fill: false,
              order: 2,
            },
            {
              label: '|z| < 1',
              data: inside.map((p) => ({ x: p.re, y: p.im })),
              showLine: false,
              pointRadius: 7,
              pointHoverRadius: 9,
              backgroundColor: isDark ? '#34d399' : '#059669',
              borderColor: isDark ? '#064e3b' : '#ecfdf5',
              borderWidth: 1.5,
              order: 1,
            },
            {
              label: '|z| ≥ 1',
              data: outside.map((p) => ({ x: p.re, y: p.im })),
              showLine: false,
              pointRadius: 7,
              pointHoverRadius: 9,
              backgroundColor: isDark ? '#fb7185' : '#e11d48',
              borderColor: isDark ? '#450a0a' : '#fff1f2',
              borderWidth: 1.5,
              order: 1,
            },
          ],
        },
      };
    }

    const b = boundsS(norm);
    const inside = norm.filter((p) => p.re < -1e-9);
    const outside = norm.filter((p) => p.re >= -1e-9);
    const showBoundary = b.xMin < 0 && b.xMax > 0;

    const ds = [];
    if (showBoundary) {
      ds.push({
        label: 'Re = 0',
        data: [
          { x: 0, y: b.yMin },
          { x: 0, y: b.yMax },
        ],
        showLine: true,
        pointRadius: 0,
        pointHoverRadius: 0,
        borderColor: isDark ? '#fbbf24' : '#ca8a04',
        borderWidth: 2,
        borderDash: [6, 4],
        fill: false,
        order: 2,
      });
    }
    ds.push(
      {
        label: 'Re < 0',
        data: inside.map((p) => ({ x: p.re, y: p.im })),
        showLine: false,
        pointRadius: 7,
        pointHoverRadius: 9,
        backgroundColor: isDark ? '#34d399' : '#059669',
        borderColor: isDark ? '#064e3b' : '#ecfdf5',
        borderWidth: 1.5,
        order: 1,
      },
      {
        label: 'Re ≥ 0',
        data: outside.map((p) => ({ x: p.re, y: p.im })),
        showLine: false,
        pointRadius: 7,
        pointHoverRadius: 9,
        backgroundColor: isDark ? '#fb7185' : '#e11d48',
        borderColor: isDark ? '#450a0a' : '#fff1f2',
        borderWidth: 1.5,
        order: 1,
      }
    );

    return {
      xMin: b.xMin,
      xMax: b.xMax,
      yMin: b.yMin,
      yMax: b.yMax,
      data: { datasets: ds },
    };
  }, [variant, poles, isDark]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'nearest', intersect: false },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: isDark ? '#cbd5e1' : '#334155',
          usePointStyle: true,
          font: { size: 10, weight: '600' },
          filter: (_item, chartData) => {
            const d = chartData.datasets[_item.datasetIndex];
            return d.data && d.data.length > 0;
          },
        },
      },
      title: { display: false },
      tooltip: {
        filter: (item) => {
          const d = item.chart.data.datasets[item.datasetIndex];
          return (d.pointRadius ?? 0) > 0;
        },
        backgroundColor: isDark ? '#0f172a' : '#ffffff',
        titleColor: isDark ? '#f8fafc' : '#0f172a',
        bodyColor: isDark ? '#cbd5e1' : '#334155',
        borderColor: isDark ? '#334155' : '#cbd5e1',
        borderWidth: 1,
        callbacks: {
          label(ctx) {
            const { x, y } = ctx.parsed;
            const lines = [`Re: ${x.toFixed(5)}`, `Im: ${y.toFixed(5)}`];
            if (variant === 'z') {
              lines.push(`|z|: ${Math.hypot(x, y).toFixed(5)}`);
            }
            return lines;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        min: xMin,
        max: xMax,
        title: {
          display: true,
          text: 'Re',
          color: isDark ? '#94a3b8' : '#475569',
          font: { size: 12, weight: '700' },
        },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: isDark ? '#94a3b8' : '#64748b' },
      },
      y: {
        type: 'linear',
        min: yMin,
        max: yMax,
        title: {
          display: true,
          text: 'Im',
          color: isDark ? '#94a3b8' : '#475569',
          font: { size: 12, weight: '700' },
        },
        grid: { color: 'rgba(71, 85, 105, 0.35)', drawBorder: false },
        ticks: { color: isDark ? '#94a3b8' : '#64748b' },
      },
    },
  };

  return (
    <div className="mx-auto h-[min(22rem,70vw)] w-full max-w-md min-h-[240px]">
      <Scatter data={data} options={options} />
    </div>
  );
}

export default StabilityPoleChart;
