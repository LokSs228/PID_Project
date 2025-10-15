import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function Sim({ sim_points, y0 }) {
const wData = sim_points.map(point => ({ x: Number(point.t), y: Number(point.w) }));
const yData = sim_points.map(point => ({ x: Number(point.t), y: Number(point.y) }));
const uData = sim_points.map(point => ({ x: Number(point.t), y: Number(point.u) }));
  const data = {
  datasets: [
    {
      label: 'Požadovaná hodnota (w)',
      data: wData,
      borderColor: 'gray',
      // остальные настройки
    },
    {
      label: 'Výstup systému (y)',
      data: yData,
      borderColor: 'blue',
      // остальные настройки
    },
    {
      label: 'Řídicí vstup (u)',
      data: uData,
      borderColor: 'green',
      yAxisID: 'y1',
      // остальные настройки
    },
    {
      label: 'Počáteční bod (y₀)',
      data: [{ x: Number(sim_points[0].t), y: Number(y0) }],
      borderColor: 'red',
      pointRadius: 5,
      showLine: false,
    },
  ],
};


  const options = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { display: true },
      title: { display: true, text: 'Graf simulace PID-regulátoru' },
      tooltip: {
        enabled: true,
        mode: 'index',
        intersect: false,
      },
    },
    scales: {
      x: {
        type: 'linear',
        title: { display: true, text: 'Čas (s)' },
      },
      y: {
        type: 'linear',
        position: 'left',
        title: { display: true, text: 'Hodnota (w a y)' },
      },
      y1: {
        type: 'linear',
        position: 'right',
        title: { display: true, text: 'Řídicí vstup (u)' },
        grid: { drawOnChartArea: false },
      },
    },
  };

  return (
    <div>
      <Line data={data} options={options} />
    </div>
  );
}
export default Sim;


