import React from 'react';
import 'katex/dist/katex.min.css';
import { BlockMath } from 'react-katex';

function TransferFunctionInput({
  onResult, method, generations, populationSize, mutationRate, controllerType, lambdaAlpha
}) {
  const [K, setK] = React.useState('');
  const [T_num, setTNum] = React.useState(['']);
  const [T_den, setTDen] = React.useState(['']);
  const [L, setL] = React.useState('');
  const [error, setError] = React.useState('');
  const [timeParams, setTimeParams] = React.useState({
    t1: 460, t2: 860, t3: 1260, t4: 1660, t5: 2060, t6: 2460, t7: 2500,
    w1: 150, w2: 170, td: 1200, d: 0,
  });
  const [y0, setY0] = React.useState(70);

  const inputStyle = "w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none transition-all";
  const labelStyle = "block text-[10px] font-bold text-slate-500 uppercase mb-1 ml-1";
  const miniInputStyle = "w-full bg-slate-900 border border-slate-800 rounded px-1.5 py-1 text-[11px] text-center focus:border-blue-500 outline-none transition-colors";

  const handleTimeParamChange = (e) => {
    const { name, value } = e.target;
    setTimeParams((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const body = {
        controllerType,
        K: parseFloat(K),
        T_num: T_num.map(val => parseFloat(val)).filter(val => !isNaN(val)),
        T_den: T_den.map(val => parseFloat(val)).filter(val => !isNaN(val)),
        Method: method,
        timeParams: Object.values(timeParams).map(parseFloat),
        y0: parseFloat(y0),
        lambdaAlpha,
      };
      if (L !== '') body.L = parseFloat(L);
      if (method === 'GA') {
        body.generations = generations;
        body.population_size = populationSize;
        body.mutation_rate = mutationRate;
      }
      const response = await fetch('/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Chyba serveru');
      onResult(data);
    } catch (err) { setError(err.message); }
  };

  const renderLatex = () => {
    if (K === '' || T_den.some(t => t === '')) return '\\text{G(s) = ...}';
    const num = T_num.filter(v => v !== '').map(v => `(${v}s + 1)`).join('\\cdot ');
    const den = T_den.filter(v => v !== '').map(v => `(${v}s + 1)`).join('\\cdot ');
    const delay = L !== '' ? `\\cdot e^{- ${L}s}` : '';
    return `G(s) = \\frac{${K}${num ? '\\cdot ' + num : ''}}{${den}}${delay}`;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Levá část: Koeficienty */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelStyle}>Zesílení (K)</label>
              <input type="number" step="any" value={K} onChange={e => setK(e.target.value)} className={inputStyle} required />
            </div>
            <div>
              <label className={labelStyle}>Dopravní zpoždění (L)</label>
              <input type="number" step="any" value={L} onChange={e => setL(e.target.value)} className={inputStyle} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className={labelStyle}>Čitatel (Tₙ)</label>
              {T_num.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input type="number" step="any" value={v} onChange={e => {
                    const n = [...T_num]; n[i] = e.target.value; setTNum(n);
                  }} className={inputStyle} />
                  {T_num.length > 1 && <button type="button" onClick={() => setTNum(T_num.filter((_, idx) => idx !== i))} className="text-slate-500 hover:text-red-400">✕</button>}
                </div>
              ))}
              <button type="button" onClick={() => setTNum([...T_num, ''])} className="text-[10px] text-blue-400 hover:text-blue-300 font-bold uppercase tracking-tighter">+ Přidat člen</button>
            </div>
            <div className="space-y-2">
              <label className={labelStyle}>Jmenovatel (T_d)</label>
              {T_den.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input type="number" step="any" value={v} onChange={e => {
                    const n = [...T_den]; n[i] = e.target.value; setTDen(n);
                  }} className={inputStyle} />
                  {T_den.length > 1 && <button type="button" onClick={() => setTDen(T_den.filter((_, idx) => idx !== i))} className="text-slate-500 hover:text-red-400">✕</button>}
                </div>
              ))}
              <button type="button" onClick={() => setTDen([...T_den, ''])} className="text-[10px] text-blue-400 hover:text-blue-300 font-bold uppercase tracking-tighter">+ Přidat člen</button>
            </div>
          </div>
        </div>

        {/* Pravá část: Scénář a Info */}
        <div className="bg-slate-900/30 p-5 rounded-xl border border-slate-700/30 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <label className={labelStyle}>Simulační scénář a porucha</label>
              
              <div className="relative group cursor-help">
                <div className="w-4 h-4 rounded-full border border-slate-500 text-slate-500 flex items-center justify-center text-[10px] font-bold hover:border-blue-400 hover:text-blue-400 transition-colors">
                  i
                </div>
                
                <div className="absolute z-50 left-0 top-6 w-80 p-4 bg-slate-800 border border-slate-700 shadow-2xl rounded-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                  <h4 className="text-blue-400 font-bold text-xs uppercase mb-3 border-b border-slate-700 pb-1">Struktura simulace</h4>
                  <div className="text-[11px] text-slate-300 space-y-3 leading-relaxed">
                    <section>
                      <span className="text-emerald-400 font-bold">Časové body (t1-t7):</span> Definuje sekvenci změn žádané hodnoty (skoky a rampy).
                    </section>
                    <section>
                      <span className="text-emerald-400 font-bold">Amplitudy (w1, w2):</span> Úrovně, kterých má systém v daných časech dosáhnout.
                    </section>
                    <section className="bg-slate-900/50 p-2 rounded border border-amber-900/30">
                      <span className="text-amber-400 font-bold block mb-1 underline">Externí porucha (td, d):</span>
                      <ul className="list-disc ml-3 space-y-1">
                        <li><span className="text-white">td:</span> Čas, kdy do systému vstoupí porucha.</li>
                        <li><span className="text-white">d:</span> Velikost poruchy (přičítá se k akční veličině regulátoru). Testuje, jak se regulátor vyrovná s nárazem.</li>
                      </ul>
                    </section>
                    <p className="text-[10px] italic text-slate-400 pt-1">
                      Pozn: Metriky kvality (překmit, IAE) se počítají z prvního skoku v čase t1.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              {/* Sekce Čas a Setpointy */}
              <div className="grid grid-cols-5 gap-2">
                {['t1','t2','t3','t4','t5','t6','t7','w1','w2','y0'].map(k => (
                  <div key={k}>
                    <input 
                      type="number" 
                      name={k} 
                      value={k === 'y0' ? y0 : timeParams[k]} 
                      onChange={k === 'y0' ? e => setY0(e.target.value) : handleTimeParamChange} 
                      className={`${miniInputStyle} ${k === 'y0' ? 'text-emerald-400 border-emerald-900/50' : 'text-slate-100'}`} 
                    />
                    <div className="text-[8px] text-slate-600 text-center uppercase mt-1 font-medium">{k}</div>
                  </div>
                ))}
              </div>

              {/* Sekce Porucha - Zvýrazněná */}
              <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                <div className="text-[9px] font-bold text-amber-500/70 uppercase mb-2 tracking-widest text-center">Nastavení poruchy (Disturbance)</div>
                <div className="flex justify-center gap-4">
                  <div className="w-24">
                    <input type="number" name="td" value={timeParams.td} onChange={handleTimeParamChange} className={`${miniInputStyle} border-amber-900/30 text-amber-200`} />
                    <div className="text-[8px] text-amber-600/60 text-center uppercase mt-1">Čas (td)</div>
                  </div>
                  <div className="w-24">
                    <input type="number" name="d" value={timeParams.d} onChange={handleTimeParamChange} className={`${miniInputStyle} border-amber-900/30 text-amber-200`} />
                    <div className="text-[8px] text-amber-600/60 text-center uppercase mt-1">Velikost (d)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-slate-950/50 rounded-lg text-blue-100 flex justify-center border border-slate-800">
            <BlockMath math={renderLatex()} />
          </div>
        </div>
      </div>

      <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black py-4 rounded-xl shadow-lg shadow-blue-900/20 transition-all uppercase tracking-[0.2em] text-sm">
        Analyzovat a vypočítat
      </button>
      {error && <p className="text-red-400 text-xs text-center">{error}</p>}
    </form>
  );
}

export default TransferFunctionInput;
