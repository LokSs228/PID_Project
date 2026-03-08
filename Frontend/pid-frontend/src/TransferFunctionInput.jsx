import React from 'react';
import 'katex/dist/katex.min.css';
import { BlockMath } from 'react-katex';

function TransferFunctionInput({
  onResult,
  onRequestStart,
  onRequestEnd,
  method,
  generations,
  populationSize,
  mutationRate,
  controllerType,
  lambdaAlpha,
}) {
  const [K, setK] = React.useState('');
  const [T_num, setTNum] = React.useState(['']);
  const [T_den, setTDen] = React.useState(['']);
  const [L, setL] = React.useState('');
  const [error, setError] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [timeParams, setTimeParams] = React.useState({
    t1: 460,
    t2: 860,
    t3: 1260,
    t4: 1660,
    t5: 2060,
    t6: 2460,
    t7: 2500,
    w1: 150,
    w2: 170,
    td: 1200,
    d: 0,
  });
  const [y0, setY0] = React.useState(70);

  const inputStyle =
    'w-full rounded-xl border border-slate-700/80 bg-slate-900/80 px-4 py-2.5 text-sm text-slate-100 transition focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30';
  const labelStyle = 'mb-1 ml-1 block text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400';
  const miniInputStyle =
    'w-full rounded-md border border-slate-700/70 bg-slate-900/90 px-1.5 py-1.5 text-center text-[11px] text-slate-100 transition focus:border-sky-500 focus:outline-none';

  const handleTimeParamChange = (e) => {
    const { name, value } = e.target;
    setTimeParams((prev) => ({ ...prev, [name]: value }));
  };

  const updateArrayValue = (setter, arr, index, value) => {
    const next = [...arr];
    next[index] = value;
    setter(next);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    if (onRequestStart) onRequestStart();

    try {
      const body = {
        controllerType,
        K: parseFloat(K),
        T_num: T_num.map((val) => parseFloat(val)).filter((val) => !isNaN(val)),
        T_den: T_den.map((val) => parseFloat(val)).filter((val) => !isNaN(val)),
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
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
      if (onRequestEnd) onRequestEnd();
    }
  };

  const renderLatex = () => {
    if (K === '' || T_den.some((t) => t === '')) return '\\text{G(s) = ...}';
    const num = T_num
      .filter((v) => v !== '')
      .map((v) => `(${v}s + 1)`)
      .join('\\cdot ');
    const den = T_den
      .filter((v) => v !== '')
      .map((v) => `(${v}s + 1)`)
      .join('\\cdot ');
    const delay = L !== '' ? `\\cdot e^{- ${L}s}` : '';
    return `G(s) = \\frac{${K}${num ? '\\cdot ' + num : ''}}{${den}}${delay}`;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section className="space-y-4 rounded-2xl border border-slate-700/50 bg-slate-900/40 p-5">
          <h3 className="text-sm font-semibold text-slate-200">Parametry přenosu</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={labelStyle}>Zesílení (K)</label>
              <input type="number" step="any" value={K} onChange={(e) => setK(e.target.value)} className={inputStyle} required />
            </div>
            <div>
              <label className={labelStyle}>Dopravní zpoždění (L)</label>
              <input type="number" step="any" value={L} onChange={(e) => setL(e.target.value)} className={inputStyle} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className={labelStyle}>Čitatel (Tn)</label>
              {T_num.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    type="number"
                    step="any"
                    value={v}
                    onChange={(e) => updateArrayValue(setTNum, T_num, i, e.target.value)}
                    className={inputStyle}
                  />
                  {T_num.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setTNum(T_num.filter((_, idx) => idx !== i))}
                      className="rounded-lg border border-slate-700 px-3 text-slate-400 transition hover:border-rose-500 hover:text-rose-300"
                      aria-label="Odstranit člen čitatele"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => setTNum([...T_num, ''])} className="text-[11px] font-semibold text-sky-400 transition hover:text-sky-300">
                + Přidat člen
              </button>
            </div>

            <div className="space-y-2">
              <label className={labelStyle}>Jmenovatel (Td)</label>
              {T_den.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    type="number"
                    step="any"
                    value={v}
                    onChange={(e) => updateArrayValue(setTDen, T_den, i, e.target.value)}
                    className={inputStyle}
                  />
                  {T_den.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setTDen(T_den.filter((_, idx) => idx !== i))}
                      className="rounded-lg border border-slate-700 px-3 text-slate-400 transition hover:border-rose-500 hover:text-rose-300"
                      aria-label="Odstranit člen jmenovatele"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => setTDen([...T_den, ''])} className="text-[11px] font-semibold text-sky-400 transition hover:text-sky-300">
                + Přidat člen
              </button>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-5">
          <div className="mb-4 flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-200">Simulační scénář a porucha</h3>

            <div className="group relative cursor-help">
              <div className="flex h-4 w-4 items-center justify-center rounded-full border border-slate-500 text-[10px] font-bold text-slate-500 transition-colors hover:border-sky-400 hover:text-sky-400">
                i
              </div>

              <div className="invisible absolute left-0 top-6 z-50 w-80 rounded-xl border border-slate-700 bg-slate-800 p-4 opacity-0 shadow-2xl transition-all duration-200 group-hover:visible group-hover:opacity-100">
                <h4 className="mb-3 border-b border-slate-700 pb-1 text-xs font-bold uppercase text-sky-400">Struktura simulace</h4>
                <div className="space-y-3 text-[11px] leading-relaxed text-slate-300">
                  <section>
                    <span className="font-bold text-emerald-400">Časové body (t1-t7):</span> Definují sekvenci změn žádané hodnoty (skoky a rampy).
                  </section>
                  <section>
                    <span className="font-bold text-emerald-400">Amplitudy (w1, w2):</span> Úrovně, kterých má systém v daných časech dosáhnout.
                  </section>
                  <section className="rounded border border-amber-900/30 bg-slate-900/50 p-2">
                    <span className="mb-1 block font-bold text-amber-400 underline">Externí porucha (td, d):</span>
                    <ul className="ml-3 list-disc space-y-1">
                      <li>
                        <span className="text-white">td:</span> Čas, kdy do systému vstoupí porucha.
                      </li>
                      <li>
                        <span className="text-white">d:</span> Velikost poruchy (přičítá se k akční veličině regulátoru). Testuje, jak se regulátor vyrovná s nárazem.
                      </li>
                    </ul>
                  </section>
                  <p className="pt-1 text-[10px] italic text-slate-400">Pozn: Metriky kvality (překmit, IAE) se počítají z prvního skoku v čase t1.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-5 gap-2">
              {['t1', 't2', 't3', 't4', 't5', 't6', 't7', 'w1', 'w2', 'y0'].map((k) => (
                <div key={k}>
                  <input
                    type="number"
                    name={k}
                    value={k === 'y0' ? y0 : timeParams[k]}
                    onChange={k === 'y0' ? (e) => setY0(e.target.value) : handleTimeParamChange}
                    className={`${miniInputStyle} ${k === 'y0' ? 'border-emerald-700/50 text-emerald-300' : 'text-slate-100'}`}
                  />
                  <div className="mt-1 text-center text-[8px] font-medium uppercase text-slate-500">{k}</div>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
              <div className="mb-2 text-center text-[10px] font-bold uppercase tracking-widest text-amber-300/80">Nastavení poruchy</div>
              <div className="mx-auto flex max-w-xs justify-center gap-4">
                <div className="w-24">
                  <input type="number" name="td" value={timeParams.td} onChange={handleTimeParamChange} className={`${miniInputStyle} border-amber-700/50 text-amber-200`} />
                  <div className="mt-1 text-center text-[8px] uppercase text-amber-300/70">Čas (td)</div>
                </div>
                <div className="w-24">
                  <input type="number" name="d" value={timeParams.d} onChange={handleTimeParamChange} className={`${miniInputStyle} border-amber-700/50 text-amber-200`} />
                  <div className="mt-1 text-center text-[8px] uppercase text-amber-300/70">Velikost (d)</div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-blue-100">
            <BlockMath math={renderLatex()} />
          </div>
        </section>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="relative flex w-full items-center justify-center rounded-xl bg-sky-600 py-4 text-sm font-black uppercase tracking-[0.18em] text-white shadow-lg shadow-sky-950/30 transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-slate-700"
      >
        {isSubmitting && <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />}
        Analyzovat a vypočítat
      </button>
      {error && <p className="text-center text-xs text-rose-400">{error}</p>}
    </form>
  );
}

export default TransferFunctionInput;
