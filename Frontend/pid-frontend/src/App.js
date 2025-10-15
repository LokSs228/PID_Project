import React, { useState } from 'react';
import TransferFunctionInput from './TransferFunctionInput';
import PidTable from './PIDtable';
import Step from './Step';
import Sim from './Sim';

function App() {
  const [pidData, setPidData] = useState(null);
  const [stepPoints, setStepPoints] = useState(null);
  const [sim_points, setSimParams] = useState(null);  // для параметров сигнала
  const [y0, setY0] = useState(null);                // для начального значения
  console.log('App sim_points:', sim_points, 'y0:', y0);
  const handleResult = (result) => {
    setPidData(result.pid);
    setStepPoints({
      points: result.step_response,
      inflection: result.inflection_point,
      tangent_line: result.tangent_line,
      A_L_points: result.A_L_points,
    });
    setSimParams(result.sim_points); // предположим, что Params есть в result
    setY0(result.y0);            // и y0 тоже есть
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Výpočet PID koeficientů</h1>

      <TransferFunctionInput onResult={handleResult} />

      {pidData && <PidTable data={pidData} />}
      {stepPoints && <Step points={stepPoints} />}

      <hr style={{ margin: '40px 0' }} />
      <h2>Nastavení požadované hodnoty</h2>

      {/* Добавляем Sim, если есть параметры и y0 */}
      {sim_points && y0 !== null && y0 !== undefined && <Sim sim_points={sim_points} y0={y0} />}
    </div>
  );
}

export default App;



