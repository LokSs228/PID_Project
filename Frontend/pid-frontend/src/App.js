import React, { useEffect, useState } from 'react';
import TransferFunctionInput from './TransferFunctionInput';
import PidTable from './PIDtable';
import Step from './Step';
import Sim from './Sim';
import MetricsTable from './MetricsTable';
import StabilityPanel from './StabilityPanel';

function App() {
  const [pidData, setPidData] = useState(null);
  const [stepPoints, setStepPoints] = useState(null);
  const [approxModel, setApproxModel] = useState(null);
  const [sim_points, setSimParams] = useState(null);
  const [y0, setY0] = useState(null);
  const [method, setMethod] = useState('ZN');
  const [generations, setGenerations] = useState(50);
  const [populationSize, setPopulationSize] = useState(20);
  const [mutationRate, setMutationRate] = useState(0.1);
  const [controllerType, setControllerType] = useState('PID');
  const [lambdaAlpha, setLambdaAlpha] = useState(2.0);
  const [metrics, setMetrics] = useState(null);
  const [stability, setStability] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('pid_theme') || 'dark');
  const isDark = theme === 'dark';

  const handleRequestStart = () => {
    setIsLoading(true);
    setPidData(null);
    setStepPoints(null);
    setApproxModel(null);
    setSimParams(null);
    setY0(null);
    setMetrics(null);
    setStability(null);
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
    setApproxModel(
      result.K !== undefined && result.T !== undefined && result.L !== undefined
        ? { K: result.K, T: result.T, L: result.L }
        : null
    );
    const st = result.stability || null;
    const showSimAndMetrics = st ? st.stable === true : !!result.closed_loop_stable;
    setSimParams(showSimAndMetrics ? result.sim_points || [] : []);
    setY0(result.y0);
    setStability(st);
    setMetrics(
      showSimAndMetrics && result.overshoot !== undefined
        ? {
            overshoot: result.overshoot,
            settlingTime: result.settlingtime,
            settlingStatus: result.settling_status,
            IAE: result.IAE,
            ITAE: result.ITAE,
          }
        : null
    );
  };

  useEffect(() => {
    localStorage.setItem('pid_theme', theme);
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
  }, [theme, isDark]);

  const panelClass = `rounded-2xl p-4 sm:p-6 ${
    isDark
      ? 'border border-slate-700/60 bg-slate-900/45 shadow-xl shadow-slate-950/30 backdrop-blur-sm'
      : 'border border-slate-200 bg-white shadow-lg shadow-slate-200/80'
  }`;
  const sectionLabel = `mb-3 block text-[10px] font-bold uppercase tracking-[0.16em] ${
    isDark ? 'text-slate-400' : 'text-slate-600'
  }`;
  const selectClass =
    `block w-full rounded-xl p-3 text-sm transition focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30 ${
      isDark
        ? 'border border-slate-700/80 bg-slate-900/80 text-slate-100 hover:border-slate-500'
        : 'border border-slate-300 bg-white text-slate-900 hover:border-slate-400'
    }`;

  const chrOptions = [
    { value: 'CHR_0_POZ_H', label: '0% prekmit, pozadavana hodnota' },
    { value: 'CHR_0_POT_P', label: '0% prekmit, potlaceni poruchy' },
    { value: 'CHR_20_POZ_H', label: '20% prekmit, pozadavana hodnota' },
    { value: 'CHR_20_POT_P', label: '20% prekmit, potlaceni poruchy' },
  ];

  const handleMethodChange = (value) => {
    setMethod(value);
  };

  return (
    <div
      className={`relative min-h-screen overflow-x-hidden px-3 py-5 sm:px-6 sm:py-6 lg:px-8 ${
        isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-100 text-slate-900'
      }`}
    >
      <div
        className={`pointer-events-none absolute -left-32 top-0 h-80 w-80 rounded-full blur-3xl ${
          isDark ? 'bg-cyan-500/15' : 'bg-cyan-400/15'
        }`}
      />
      <div
        className={`pointer-events-none absolute -right-36 top-36 h-96 w-96 rounded-full blur-3xl ${
          isDark ? 'bg-amber-500/10' : 'bg-amber-400/15'
        }`}
      />

      <div className="mx-auto max-w-[1600px] space-y-8">
        <header
          className={`rounded-2xl p-6 ${
            isDark
              ? 'border border-slate-800/80 bg-slate-900/65 shadow-lg shadow-black/20'
              : 'border border-slate-200 bg-white shadow-lg shadow-slate-200/80'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className={`text-3xl font-black tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>PIDtuner</h1>
            </div>
            <button
              type="button"
              onClick={() => setTheme(isDark ? 'light' : 'dark')}
              className={`rounded-xl border px-4 py-2 text-xs font-bold uppercase tracking-[0.14em] transition ${
                isDark
                  ? 'border-slate-600 bg-slate-800 text-slate-200 hover:border-sky-400 hover:text-sky-300'
                  : 'border-slate-300 bg-white text-slate-700 hover:border-sky-500 hover:text-sky-700'
              }`}
            >
              {isDark ? 'Světlý režim' : 'Tmavý režim'}
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-8 xl:grid-cols-3">
          <section className={`${panelClass} xl:col-span-1`}>
            <h2 className={sectionLabel}>Nastavení výpočtu</h2>

            <div className="space-y-4">
              <div>
                <label className={sectionLabel}>Metoda ladeni</label>
                <select value={method} onChange={(e) => handleMethodChange(e.target.value)} className={selectClass}>
                  <option value="ZN">Ziegler-Nichols</option>
                  <option value="GA">Geneticky algoritmus</option>
                  <optgroup label="CHR">
                    {chrOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </optgroup>
                  <option value="IMC">IMC / Lambda</option>
                </select>
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
                <div
                  className={`space-y-4 rounded-xl p-4 ${
                    isDark ? 'border border-slate-700/60 bg-slate-900/60' : 'border border-slate-200 bg-slate-50'
                  }`}
                >
                  <div className="space-y-2">
                    <div className={`flex items-center justify-between text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                      <span>Generace</span>
                      <span className={`font-mono ${isDark ? 'text-sky-300' : 'text-sky-700'}`}>{generations}</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="200"
                      step="10"
                      value={generations}
                      onChange={(e) => setGenerations(parseInt(e.target.value))}
                      className={`h-1.5 w-full cursor-pointer appearance-none rounded-lg ${isDark ? 'bg-slate-700 accent-sky-500' : 'bg-slate-300 accent-sky-600'}`}
                    />
                  </div>

                  <div className="space-y-2">
                    <div className={`flex items-center justify-between text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                      <span>Velikost populace</span>
                      <span className={`font-mono ${isDark ? 'text-sky-300' : 'text-sky-700'}`}>{populationSize}</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="100"
                      step="5"
                      value={populationSize}
                      onChange={(e) => setPopulationSize(parseInt(e.target.value))}
                      className={`h-1.5 w-full cursor-pointer appearance-none rounded-lg ${isDark ? 'bg-slate-700 accent-sky-500' : 'bg-slate-300 accent-sky-600'}`}
                    />
                  </div>

                  <div className="space-y-2">
                    <div className={`flex items-center justify-between text-[11px] uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                      <span>Mutace</span>
                      <span className={`font-mono ${isDark ? 'text-sky-300' : 'text-sky-700'}`}>{mutationRate.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={mutationRate}
                      onChange={(e) => setMutationRate(parseFloat(e.target.value))}
                      className={`h-1.5 w-full cursor-pointer appearance-none rounded-lg ${isDark ? 'bg-slate-700 accent-sky-500' : 'bg-slate-300 accent-sky-600'}`}
                    />
                  </div>
                </div>
              )}

              {method === 'IMC' && (
                <div className={`rounded-xl p-4 ${isDark ? 'border border-slate-700/60 bg-slate-900/60' : 'border border-slate-200 bg-slate-50'}`}>
                  <label className={sectionLabel}>Lambda parametr (α)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={lambdaAlpha}
                    onChange={(e) => setLambdaAlpha(parseFloat(e.target.value))}
                    className={selectClass}
                  />
                  <p className={`mt-2 text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Lambda = α × L nebo α × Tdom</p>
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
              theme={theme}
            />
          </section>
        </div>

        {isLoading && (
          <div className={`flex flex-col items-center justify-center rounded-2xl py-14 ${isDark ? 'border border-slate-700/60 bg-slate-900/45' : 'border border-slate-200 bg-white'}`}>
            <div className={`h-12 w-12 animate-spin rounded-full border-4 ${isDark ? 'border-slate-700 border-t-sky-400' : 'border-slate-300 border-t-sky-500'}`} />
            <p className={`mt-4 text-sm uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Načítání výsledků...</p>
          </div>
        )}

        {!isLoading && (pidData || stepPoints) && (
          <div className="space-y-8 pb-12">
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
              <section className={`${panelClass} lg:col-span-4`}>
                <h2 className={sectionLabel}>Vypočtené koeficienty</h2>
                <PidTable data={pidData} theme={theme} />
              </section>

              <section className={`${panelClass} lg:col-span-8`}>
                <h2 className={sectionLabel}>Přechodová charakteristika systému</h2>
                <div className="h-[360px] sm:h-[420px]">
                  <Step points={stepPoints} approxModel={approxModel} theme={theme} />
                </div>
              </section>
            </div>

            {stability && <StabilityPanel stability={stability} theme={theme} />}

            {stability?.stable && (
              <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
                <section className={`${panelClass} lg:col-span-9`}>
                  <h2 className={`${sectionLabel} text-center`}>Simulace regulačního pochodu s PID regulátorem</h2>
                  <div className="h-[360px] sm:h-[520px]">
                    <Sim sim_points={sim_points} y0={y0} theme={theme} />
                  </div>
                </section>

                <section className={`${panelClass} lg:col-span-3`}>
                  <h2 className={sectionLabel}>Kvalita regulace</h2>
                  {metrics && <MetricsTable metrics={metrics} theme={theme} />}
                  <div
                    className={`mt-5 rounded-xl border border-sky-500/20 bg-sky-500/5 p-4 text-[11px] italic leading-relaxed ${
                      isDark ? 'text-slate-400' : 'text-slate-600'
                    }`}
                  >
                    IAE a ITAE charakterizují celkovou regulační chybu. Čím nižší hodnota, tím kvalitnější nastavení.
                  </div>
                </section>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;




