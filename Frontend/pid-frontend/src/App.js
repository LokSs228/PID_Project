import React, { useEffect, useRef, useState } from 'react';
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
  const [chrVariant, setChrVariant] = useState('CHR_0_POZ_H');
  const [isMethodOpen, setIsMethodOpen] = useState(false);
  const [isChrExpanded, setIsChrExpanded] = useState(false);
  const [generations, setGenerations] = useState(50);
  const [populationSize, setPopulationSize] = useState(20);
  const [mutationRate, setMutationRate] = useState(0.1);
  const [controllerType, setControllerType] = useState('PID');
  const [lambdaAlpha, setLambdaAlpha] = useState(2.0);
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRequestStart = () => {
    setIsLoading(true);
    setPidData(null);
    setStepPoints(null);
    setSimParams(null);
    setY0(null);
    setMetrics(null);
  };

  const handleRequestEnd = () => {
    setIsLoading(false);
  };

  const handleResult = (result) => {
    setPidData(result.pid);
    setStepPoints({
      points: result.step_response,
      apro_points: result.apro_step_response || [],
    });
    setSimParams(result.sim_points);
    setY0(result.y0);
    setMetrics(
      result.overshoot !== undefined
        ? {
            overshoot: result.overshoot,
            settlingTime: result.settlingtime,
            IAE: result.IAE,
            ITAE: result.ITAE,
          }
        : null
    );
  };

  const panelClass = 'rounded-2xl border border-slate-700/60 bg-slate-900/45 p-4 shadow-xl shadow-slate-950/30 backdrop-blur-sm sm:p-6';
  const sectionLabel = 'mb-3 block text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400';
  const selectClass =
    'block w-full rounded-xl border border-slate-700/80 bg-slate-900/80 p-3 text-sm text-slate-100 transition hover:border-slate-500 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30';

  const methodGroup = method.startsWith('CHR_') ? 'CHR' : method;
  const methodDropdownRef = useRef(null);

  const chrOptions = [
    { value: 'CHR_0_POZ_H', label: '0% prekmit, pozadavana hodnota' },
    { value: 'CHR_0_POT_P', label: '0% prekmit, potlaceni poruchy' },
    { value: 'CHR_20_POZ_H', label: '20% prekmit, pozadavana hodnota' },
    { value: 'CHR_20_POT_P', label: '20% prekmit, potlaceni poruchy' },
  ];

  const methodLabels = {
    ZN: 'Ziegler-Nichols',
    GA: 'Geneticky algoritmus',
    IMC: 'IMC / Lambda',
  };

  const handleMethodGroupChange = (value) => {
    if (value === 'CHR') {
      setMethod(chrVariant);
      return;
    }
    setMethod(value);
  };

  const handleChrVariantChange = (value) => {
    setChrVariant(value);
    setMethod(value);
  };

  const handleMethodSelect = (value) => {
    if (value === 'CHR') {
      setIsChrExpanded((prev) => !prev);
      return;
    }
    handleMethodGroupChange(value);
    setIsMethodOpen(false);
    setIsChrExpanded(false);
  };

  const handleChrSelect = (value) => {
    handleChrVariantChange(value);
    setIsMethodOpen(false);
    setIsChrExpanded(true);
  };

  const currentMethodLabel = () => {
    if (methodGroup === 'CHR') {
      const currentChr = chrOptions.find((option) => option.value === method);
      return currentChr ? `CHR ${currentChr.label}` : 'CHR';
    }
    return methodLabels[method] || method;
  };

  useEffect(() => {
    if (methodGroup === 'CHR') {
      setIsChrExpanded(true);
    }
  }, [methodGroup]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (methodDropdownRef.current && !methodDropdownRef.current.contains(event.target)) {
        setIsMethodOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-slate-950 px-3 py-5 text-slate-100 sm:px-6 sm:py-6 lg:px-8">
      <div className="pointer-events-none absolute -left-32 top-0 h-80 w-80 rounded-full bg-cyan-500/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-36 top-36 h-96 w-96 rounded-full bg-amber-500/10 blur-3xl" />

      <div className="mx-auto max-w-[1600px] space-y-8">
        <header className="rounded-2xl border border-slate-800/80 bg-slate-900/65 p-6 shadow-lg shadow-black/20">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white">PIDtuner</h1>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-8 xl:grid-cols-3">
          <section className={`${panelClass} xl:col-span-1`}>
            <h2 className={sectionLabel}>Nastavení výpočtu</h2>

            <div className="space-y-4">
              <div className="relative" ref={methodDropdownRef}>
                <label className={sectionLabel}>Metoda ladeni</label>
                <button
                  type="button"
                  className={`${selectClass} flex items-center justify-between text-left`}
                  onClick={() => setIsMethodOpen((prev) => !prev)}
                >
                  <span>{currentMethodLabel()}</span>
                  <span className="ml-4 text-slate-400">v</span>
                </button>

                {isMethodOpen && (
                  <div className="absolute z-20 mt-2 w-full rounded-xl border border-slate-700/80 bg-slate-900/95 p-2 shadow-xl shadow-slate-950/40 backdrop-blur-sm">
                    <button
                      type="button"
                      className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-100 hover:bg-slate-800/80"
                      onClick={() => handleMethodSelect('ZN')}
                    >
                      Ziegler-Nichols
                    </button>
                    <button
                      type="button"
                      className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-100 hover:bg-slate-800/80"
                      onClick={() => handleMethodSelect('GA')}
                    >
                      Geneticky algoritmus
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm text-slate-100 hover:bg-slate-800/80"
                      onClick={() => handleMethodSelect('CHR')}
                    >
                      <span>CHR</span>
                      <span className="text-slate-400">{isChrExpanded ? '^' : 'v'}</span>
                    </button>
                    {isChrExpanded && (
                      <div className="mt-1 space-y-1 border-l border-slate-700/70 pl-3">
                        {chrOptions.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            className={`w-full rounded-lg px-3 py-2 text-left text-sm ${
                              method === option.value ? 'bg-slate-800/80 text-sky-200' : 'text-slate-200 hover:bg-slate-800/60'
                            }`}
                            onClick={() => handleChrSelect(option.value)}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    )}
                    <button
                      type="button"
                      className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-100 hover:bg-slate-800/80"
                      onClick={() => handleMethodSelect('IMC')}
                    >
                      IMC / Lambda
                    </button>
                  </div>
                )}
              </div>

              <div>
                <label className={sectionLabel}>Typ regulátoru</label>
                <select value={controllerType} onChange={(e) => setControllerType(e.target.value)} className={selectClass}>
                  <option value="PID">PID</option>
                  <option value="PI">PI</option>
                  <option value="PD">PD</option>
                  <option value="P">P</option>
                </select>
              </div>

              {method === 'GA' && (
                <div className="space-y-4 rounded-xl border border-slate-700/60 bg-slate-900/60 p-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-slate-400">
                      <span>Generace</span>
                      <span className="font-mono text-sky-300">{generations}</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="200"
                      step="10"
                      value={generations}
                      onChange={(e) => setGenerations(parseInt(e.target.value))}
                      className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-700 accent-sky-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-slate-400">
                      <span>Velikost populace</span>
                      <span className="font-mono text-sky-300">{populationSize}</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="100"
                      step="5"
                      value={populationSize}
                      onChange={(e) => setPopulationSize(parseInt(e.target.value))}
                      className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-700 accent-sky-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-slate-400">
                      <span>Mutace</span>
                      <span className="font-mono text-sky-300">{mutationRate.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={mutationRate}
                      onChange={(e) => setMutationRate(parseFloat(e.target.value))}
                      className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-700 accent-sky-500"
                    />
                  </div>
                </div>
              )}

              {method === 'IMC' && (
                <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 p-4">
                  <label className={sectionLabel}>Lambda parametr (α)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={lambdaAlpha}
                    onChange={(e) => setLambdaAlpha(parseFloat(e.target.value))}
                    className={selectClass}
                  />
                  <p className="mt-2 text-xs text-slate-500">Lambda = α × L nebo α × Tdom</p>
                </div>
              )}
            </div>
          </section>

          <section className={`${panelClass} xl:col-span-2`}>
            <h2 className={sectionLabel}>Identifikace a model řízeného systému G(s)</h2>
            <TransferFunctionInput
              onResult={handleResult}
              onRequestStart={handleRequestStart}
              onRequestEnd={handleRequestEnd}
              method={method}
              generations={generations}
              populationSize={populationSize}
              mutationRate={mutationRate}
              controllerType={controllerType}
              lambdaAlpha={lambdaAlpha}
            />
          </section>
        </div>

        {isLoading && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-700/60 bg-slate-900/45 py-14">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-700 border-t-sky-400" />
            <p className="mt-4 text-sm uppercase tracking-[0.16em] text-slate-400">Načítání výsledků...</p>
          </div>
        )}

        {!isLoading && (pidData || stepPoints) && (
          <div className="space-y-8 pb-12">
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
              <section className={`${panelClass} lg:col-span-4`}>
                <h2 className={sectionLabel}>Vypočtené koeficienty</h2>
                <PidTable data={pidData} />
              </section>

              <section className={`${panelClass} lg:col-span-8`}>
                <h2 className={sectionLabel}>Přechodová charakteristika systému</h2>
                <div className="h-[320px] sm:h-[420px]">
                  <Step points={stepPoints} />
                </div>
              </section>
            </div>

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
              <section className={`${panelClass} lg:col-span-9`}>
                <h2 className={`${sectionLabel} text-center`}>Simulace regulačního pochodu s PID regulátorem</h2>
                <div className="h-[360px] sm:h-[520px]">
                  <Sim sim_points={sim_points} y0={y0} />
                </div>
              </section>

              <section className={`${panelClass} lg:col-span-3`}>
                <h2 className={sectionLabel}>Kvalita regulace</h2>
                {metrics && <MetricsTable metrics={metrics} />}
                <div className="mt-5 rounded-xl border border-sky-500/20 bg-sky-500/5 p-4 text-[11px] italic leading-relaxed text-slate-400">
                  IAE a ITAE charakterizují celkovou regulační chybu. Čím nižší hodnota, tím kvalitnější nastavení.
                </div>
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;



