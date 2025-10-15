import React, { useState } from 'react';
import TransferFunctionInput from './TransferFunctionInput';
import PidTable from './PIDtable';
import Step from './Step';
import Sim from './Sim';

function App() {
  const [pidData, setPidData] = useState(null);
  const [stepPoints, setStepPoints] = useState(null);
  const [sim_points, setSimParams] = useState(null);
  const [y0, setY0] = useState(null);
  const [method, setMethod] = useState('ZN');
  const [generations, setGenerations] = useState(50);
  const [populationSize, setPopulationSize] = useState(20);
  const [mutationRate, setMutationRate] = useState(0.1);


  const handleResult = (result) => {
    setPidData(result.pid);
    setStepPoints({
      points: result.step_response,
      inflection: result.inflection_point,
      tangent_line: result.tangent_line,
      A_L_points: result.A_L_points,
    });
    setSimParams(result.sim_points);
    setY0(result.y0);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Výpočet PID koeficientů</h1>

      {/* Выбор метода PID */}
      <div style={{ marginBottom: 20 }}>
        <label>
          Metoda nastavení PID:
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            style={{ marginLeft: 10 }}
          >
            <option value="ZN">Ziegler–Nichols</option>
            <option value="GA">Genetic Algorithm</option>
          </select>
        </label>
      </div>
     {method === 'GA' && (
  <div style={{ marginBottom: 20 }}>
    <h3>Parametry genetického algoritmu:</h3>
    <label>
      Generations:
      <input
        type="number"
        value={generations}
        onChange={(e) => setGenerations(parseInt(e.target.value))}
        style={{ marginLeft: 10 }}
      />
    </label>
    <br />
    <label>
      Population Size:
      <input
        type="number"
        value={populationSize}
        onChange={(e) => setPopulationSize(parseInt(e.target.value))}
        style={{ marginLeft: 10 }}
      />
    </label>
    <br />
    <label>
      Mutation Rate:
      <input
        type="number"
        step="0.01"
        value={mutationRate}
        onChange={(e) => setMutationRate(parseFloat(e.target.value))}
        style={{ marginLeft: 10 }}
      />
    </label>
  </div>
)}
 

      {/* Форма для ввода передаточной функции */}
      <TransferFunctionInput
       onResult={handleResult}
       method={method}
       generations={generations}
       populationSize={populationSize}
       mutationRate={mutationRate}
      />

      {pidData && <PidTable data={pidData} />}
      {stepPoints && <Step points={stepPoints} />}

      <hr style={{ margin: '40px 0' }} />
      <h2>Nastavení požadované hodnoty</h2>

      {sim_points && y0 !== null && <Sim sim_points={sim_points} y0={y0} />}
    </div>
  );
}

export default App;





