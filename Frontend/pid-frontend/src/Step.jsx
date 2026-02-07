import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function Step({ points }) {
  const pointArray = points.points;
  const inflection = points.inflection;
  const tangent = points.tangent_line;
  const A_L = points.A_L_points;

  if (!pointArray || pointArray.length === 0) return null;

  // Рассчитаем касательную линию
  let tangentData = [];
  if (inflection && tangent) {
    const tMax = pointArray[pointArray.length - 1].t;
    const tMin = Math.max(inflection.t - 0.2 * tMax, 0);
    const tMaxExt = inflection.t + 0.2 * tMax;

    const yMin = tangent.slope * (tMin - inflection.t) + inflection.y;
    const yMax = tangent.slope * (tMaxExt - inflection.t) + inflection.y;

    tangentData = [
      { x: tMin, y: yMin },
      { x: tMaxExt, y: yMax }
    ];
  }

  const data = {
    datasets: [
      {
        label: 'Přechodová charakteristika y(t)',
        data: pointArray.map(p => ({ x: p.t, y: p.y })),
        borderColor: 'blue',
        backgroundColor: 'lightblue',
        fill: false,
        tension: 0.3,
        pointRadius: 0,
      },
      inflection && {
        label: 'Inflexní bod',
        data: [{ x: inflection.t, y: inflection.y }],
        pointRadius: 6,
        pointBackgroundColor: 'red',
        pointBorderColor: 'darkred',
        showLine: false,
        parsing: false,
      },
      A_L && {
        label: 'A (průsečík s osou Y)',
        data: [{ x: 0, y: A_L.A }],
        pointRadius: 6,
        pointBackgroundColor: 'green',
        pointBorderColor: 'darkgreen',
        showLine: false,
        parsing: false,
      },
      A_L && {
        label: 'L (průsečík s osou X)',
        data: [{ x: A_L.L, y: 0 }],
        pointRadius: 6,
        pointBackgroundColor: 'orange',
        pointBorderColor: 'darkorange',
        showLine: false,
        parsing: false,
    },
      tangentData.length > 0 && {
        label: 'Tečna',
        data: tangentData,
        borderColor: 'red',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
        tension: 0,
      }
    ].filter(Boolean),
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Přechodová charakteristika' },
    },
    scales: {
      x: { type: 'linear', title: { display: true, text: 'Čas, s' } },
      y: { title: { display: true, text: 'Výstup y(t)' } },
    },
  };

  return <Line data={data} options={options} />;
}

export default Step;