import React, { useState } from 'react';
import TransferFunctionInput from './TransferFunctionInput';
import PidTable from './PIDtable';
import Step from './Step';
import Sim from './Sim';
import MetricsTable from './MetricsTable';

function App() {
  const [pidData, setPidData] = useState(null);
  const [stepPoints, setStepPoints] = useState(null);
  const [sim_points, setSimParams] = useState(null);
  const [y0, setY0] = useState(null);
  const [method, setMethod] = useState('ZN');
  const [generations, setGenerations] = useState(50);
  const [populationSize, setPopulationSize] = useState(20);
  const [mutationRate, setMutationRate] = useState(0.1);
  const [controllerType, setControllerType] = useState('PID');
  const [lambdaAlpha, setLambdaAlpha] = useState(2.0);
  const [metrics, setMetrics] = useState(null);

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
    setMetrics(result.overshoot !== undefined ? {
      overshoot: result.overshoot,
      settlingTime: result.settlingtime,
      IAE: result.IAE,
      ITAE: result.ITAE
    } : null);
  };

  const cardStyle = "bg-slate-800/40 border border-slate-700/50 shadow-xl rounded-2xl p-6 backdrop-blur-md";
  const labelStyle = "block text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-2";
  const selectStyle = "bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-xl focus:ring-2 focus:ring-blue-500 outline-none block w-full p-3 transition-all cursor-pointer hover:border-slate-500";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 py-6 px-4 sm:px-8">
      <div className="max-w-[1600px] mx-auto space-y-8">
        <header className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-black text-white tracking-tighter">PID <span className="text-blue-500">TUNER</span></h1>
          </div>
        </header>

        {/* Верхняя панель: Настройки и Ввод функции в одну строку */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-1 space-y-8">
            <section className={cardStyle}>
              <h2 className={labelStyle}>1. Nastavení výpočtu a regulátoru</h2>
              <div className="space-y-4">
                <div>
                  <select value={method} onChange={(e) => setMethod(e.target.value)} className={selectStyle}>
                    <option value="ZN">Ziegler–Nichols</option>
                    <option value="GA">Genetic Algorithm</option>
                    <option value="CHR_0">CHR (0 % overshoot)</option>
                    <option value="CHR_20">CHR (20 % overshoot)</option>
                    <option value="IMC">IMC / Lambda</option>
                  </select>
                </div>
                <div>
                  <select value={controllerType} onChange={(e) => setControllerType(e.target.value)} className={selectStyle}>
                    <option value="PID">PID</option>
                    <option value="PI">PI</option>
                    <option value="PD">PD</option>
                    <option value="P">P</option>
                  </select>
                </div>

                {/* Условные параметры */}
                {method === 'GA' && (
                  <div className="grid grid-cols-1 gap-4 animate-in slide-in-from-top-2 duration-300">
                    {/* Generations */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Generace: <span className="text-blue-400 font-mono text-sm">{generations}</span>
                      </div>
                      <input 
                        type="range" min="10" max="200" step="10"
                        value={generations} 
                        onChange={(e) => setGenerations(parseInt(e.target.value))} 
                        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                      />
                    </div>

                    {/* Population Size */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Populace: <span className="text-blue-400 font-mono text-sm">{populationSize}</span>
                      </div>
                      <input 
                        type="range" min="10" max="100" step="5"
                        value={populationSize} 
                        onChange={(e) => setPopulationSize(parseInt(e.target.value))} 
                        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                      />
                    </div>

                    {/* Mutation Rate */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Mutace: <span className="text-blue-400 font-mono text-sm">{mutationRate.toFixed(2)}</span>
                      </div>
                      <input 
                        type="range" min="0" max="1" step="0.01" 
                        value={mutationRate} 
                        onChange={(e) => setMutationRate(parseFloat(e.target.value))} 
                        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                      />
                    </div>
                  </div>
                )}

                {method === 'IMC' && (
                  <div className="flex flex-col gap-2 animate-in slide-in-from-top-2 duration-300">
                    <span className="text-[11px] text-purple-400 font-bold uppercase tracking-wider">λ Parameter (α)</span>
                    <input 
                      type="number" step="0.1" 
                      value={lambdaAlpha} 
                      onChange={(e) => setLambdaAlpha(parseFloat(e.target.value))} 
                      className={selectStyle} 
                    />
                    <p className="text-[10px] text-slate-500 italic">λ = α * L nebo α * T_dom</p>
                  </div>
                )}
              </div>
            </section>
          </div>

          <div className="xl:col-span-2">
            <section className={cardStyle}>
              <h2 className={labelStyle}>2. Identifikace a model řízeného systému G(s)</h2>
              <TransferFunctionInput
                onResult={handleResult}
                method={method}
                generations={generations}
                populationSize={populationSize}
                mutationRate={mutationRate}
                controllerType={controllerType}
                lambdaAlpha={lambdaAlpha}
              />
            </section>
          </div>
        </div>

        {/* Результаты: теперь они занимают больше места */}
        {(pidData || stepPoints) && (
          <div className="space-y-8 animate-in fade-in duration-500 pb-12">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Коэффициенты (узкая колонка) */}
              <div className="lg:col-span-4 h-full">
                <div className={`${cardStyle} h-full`}>
                  <h2 className={labelStyle}>Vypočtené Koeficienty</h2>
                  <PidTable data={pidData} />
                </div>
              </div>
              {/* Характеристика (широкая колонка) */}
              <div className="lg:col-span-8">
                <div className={cardStyle}>
                  <h2 className={labelStyle}>Přechodová charakteristika řízeného systému G(s)</h2>
                  <div className="h-[400px]">
                    <Step points={stepPoints} />
                  </div>
                </div>
              </div>
            </div>

            {/* Симуляция и Метрики разделены по горизонтали */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-12">
              <div className="lg:col-span-9">
                <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl shadow-inner">
                  <h2 className={`${labelStyle} mb-6 text-center`}>Simulace regulačního pochodu s PID regulátorem</h2>
                  <div className="h-[500px]">
                     <Sim sim_points={sim_points} y0={y0} />
                  </div>
                </div>
              </div>
              <div className="lg:col-span-3">
                <div className="sticky top-6 space-y-6">
                   <h2 className={labelStyle}>Kvalita Regulace</h2>
                   {metrics && <MetricsTable metrics={metrics} />}
                   <div className="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/20 text-[11px] text-slate-400 italic leading-relaxed">
                     * Měřítka IAE и ITAE indikují celkovou chybu regulace. Čím nižší hodnota, tím přesnější je nastavení.
                   </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;