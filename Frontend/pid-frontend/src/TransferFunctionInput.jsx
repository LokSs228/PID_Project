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
    w1: 150, w2: 170,
  });
  const [y0, setY0] = React.useState(70);

  const inputStyle = "w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none transition-all";
  const labelStyle = "block text-[10px] font-bold text-slate-500 uppercase mb-1 ml-1";

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
        {/* Левая часть: Коэффициенты */}
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

{/* ПРАВАЯ ЧАСТЬ: Вставляем новый блок с подсказкой здесь */}
        <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-700/30 relative group/info">
          <div className="flex items-center gap-2 mb-2">
            <label className={labelStyle}>Simulační scénář (t, w, y₀)</label>
            
            {/* Иконка "i" */}
            <div className="relative group cursor-help">
              <div className="w-4 h-4 rounded-full border border-slate-500 text-slate-500 flex items-center justify-center text-[10px] font-bold hover:border-blue-400 hover:text-blue-400 transition-colors">
                i
              </div>
              
              {/* Тултип */}
              <div className="absolute z-50 left-0 top-6 w-72 p-4 bg-slate-800 border border-slate-700 shadow-2xl rounded-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                <h4 className="text-blue-400 font-bold text-xs uppercase mb-2 text-left">Informace o simulaci</h4>
                <div className="text-[11px] text-slate-300 space-y-2 leading-relaxed text-left">
                  <p>
                    Simulace testuje robustnost regulátoru pomocí řady změn: 
                    <span className="text-white"> skok nahoru/dolů</span>, následovaný 
                    <span className="text-white"> rampou nahoru/dolů</span>.
                  </p>
                  <p>
                    <strong className="text-emerald-400">t1 – t7:</strong> Časové body, ve kterých dochází ke změně požadované hodnoty.
                  </p>
                  <p>
                    <strong className="text-emerald-400">w1, w2:</strong> Amplitudy požadovaných hodnot (setpointů).
                  </p>
                  <p className="pt-2 border-t border-slate-700 text-amber-400 font-medium italic">
                    Důležité: Výpočet metrik (IAE, ITAE, překmit) se provádí na základě odezvy na první skok v čase t1.
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-5 gap-2 mt-2">
            {['t1','t2','t3','t4','t5','t6','t7','w1','w2'].map(k => (
              <div key={k}>
                <input type="number" name={k} value={timeParams[k]} onChange={handleTimeParamChange} className="w-full bg-slate-900 border border-slate-800 rounded px-1.5 py-1 text-[11px] text-center" />
                <div className="text-[8px] text-slate-600 text-center uppercase mt-0.5">{k}</div>
              </div>
            ))}
            <div>
              <input type="number" value={y0} onChange={e => setY0(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded px-1.5 py-1 text-[11px] text-center text-emerald-400" />
              <div className="text-[8px] text-slate-600 text-center uppercase mt-0.5">y0</div>
            </div>
          </div>
          <div className="mt-6 p-4 bg-slate-950/50 rounded-lg text-blue-100 flex justify-center">
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
