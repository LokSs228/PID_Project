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
  theme,
}) {
  const isDark = theme === 'dark';
  const [K, setK] = React.useState('1');
  const [T_num, setTNum] = React.useState(['']);
  const [T_den, setTDen] = React.useState(['1']);
  const [L, setL] = React.useState('1');
  const [diffOrder, setDiffOrder] = React.useState('');
  const [intOrder, setIntOrder] = React.useState('');
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

  const inputStyle = `w-full rounded-xl px-4 py-2.5 text-sm transition focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30 ${
    isDark ? 'border border-slate-700/80 bg-slate-900/80 text-slate-100' : 'border border-slate-300 bg-white text-slate-900'
  }`;
  const labelStyle = `mb-1 ml-1 block text-[10px] font-bold uppercase tracking-[0.12em] ${isDark ? 'text-slate-400' : 'text-slate-600'}`;
  const miniInputStyle = `w-full rounded-md px-1.5 py-1.5 text-center text-[11px] transition focus:border-sky-500 focus:outline-none ${
    isDark ? 'border border-slate-700/70 bg-slate-900/90 text-slate-100' : 'border border-slate-300 bg-white text-slate-900'
  }`;

  /** Musí odpovídat pořadí v Backendu: Params[6] = t7, Params[9]=td, Params[10]=d (y0 se neposílá zde). */
  const CALC_TIME_PARAM_KEYS = ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 'w1', 'w2', 'td', 'd'];

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
        K,
        T_num: T_num.filter((val) => val !== ''),
        T_den: T_den.filter((val) => val !== ''),
        Method: method,
        timeParams: CALC_TIME_PARAM_KEYS.map((key) => parseFloat(timeParams[key])),
        y0: parseFloat(y0),
        lambdaAlpha,
      };

      if (L !== '') body.L = L;
      if (diffOrder !== '') body.diffOrder = diffOrder;
      if (intOrder !== '') body.intOrder = intOrder;

      if (method === 'GA') {
        body.generations = generations;
        body.population_size = populationSize;
        body.mutation_rate = mutationRate;
      }

      const apiBaseUrl = (process.env.REACT_APP_API_URL || '').trim().replace(/\/+$/, '');
      const calculateUrl = apiBaseUrl ? `${apiBaseUrl}/calculate` : '/calculate';

      const response = await fetch(calculateUrl, {
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
    const formatCoeff = (val) => {
      const text = String(val).trim().replace(/j/gi, 'i');
      const isComplex = /[ij]/i.test(text);
      return isComplex ? `\\left(${text}\\right)` : text;
    };
    const num = T_num
      .filter((v) => v !== '')
      .map((v) => `(${formatCoeff(v)}s + 1)`)
      .join('\\cdot ');
    const den = T_den
      .filter((v) => v !== '')
      .map((v) => `(${formatCoeff(v)}s + 1)`)
      .join('\\cdot ');
    const diffPow = diffOrder !== '' ? parseInt(diffOrder, 10) : 0;
    const intPow = intOrder !== '' ? parseInt(intOrder, 10) : 0;
    const diffTerm = diffPow > 0 ? `s^{${diffPow}}` : '';
    const intTerm = intPow > 0 ? `s^{${intPow}}` : '';
    const numWithDiff = [diffTerm, num].filter(Boolean).join('\\cdot ');
    const denWithInt = [intTerm, den].filter(Boolean).join('\\cdot ');
    const delay = L !== '' ? `\\cdot e^{- ${L}s}` : '';
    return `G(s) = \\frac{${K}${numWithDiff ? '\\cdot ' + numWithDiff : ''}}{${denWithInt || '1'}}${delay}`;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section className={`space-y-4 rounded-2xl p-5 ${isDark ? 'border border-slate-700/50 bg-slate-900/40' : 'border border-slate-200 bg-white'}`}>
          <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>Parametry přenosu</h3>
          <p className={`text-[11px] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Podporovány jsou komplexní hodnoty ve tvaru <span className={`font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>a+bi</span> nebo{" "}
            <span className={`font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>a-bi</span>. Při použití komplexních členů zadávej i{" "}
            <span className={`font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>sdružené dvojice</span>, aby výsledný polynom byl reálný.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={labelStyle}>Zesílení (K)</label>
              <input type="text" value={K} onChange={(e) => setK(e.target.value)} className={inputStyle} required />
            </div>
            <div>
              <label className={labelStyle}>Dopravní zpoždění (L)</label>
              <input type="text" value={L} onChange={(e) => setL(e.target.value)} className={inputStyle} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className={labelStyle}>Čitatel (Tn)</label>
              {T_num.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    type="text"
                    value={v}
                    onChange={(e) => updateArrayValue(setTNum, T_num, i, e.target.value)}
                    className={inputStyle}
                  />
                  {T_num.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setTNum(T_num.filter((_, idx) => idx !== i))}
                      className={`rounded-lg border px-3 transition ${
                        isDark
                          ? 'border-slate-700 text-slate-400 hover:border-rose-500 hover:text-rose-300'
                          : 'border-slate-300 text-slate-700 hover:border-rose-500 hover:text-rose-600'
                      }`}
                      aria-label="Odstranit člen čitatele"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={() => setTNum([...T_num, ''])}
                className={`text-[11px] font-semibold transition ${isDark ? 'text-sky-400 hover:text-sky-300' : 'text-sky-700 hover:text-sky-600'}`}
              >
                + Přidat člen
              </button>
            </div>

            <div className="space-y-2">
              <label className={labelStyle}>Jmenovatel (Td)</label>
              {T_den.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    type="text"
                    value={v}
                    onChange={(e) => updateArrayValue(setTDen, T_den, i, e.target.value)}
                    className={inputStyle}
                  />
                  {T_den.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setTDen(T_den.filter((_, idx) => idx !== i))}
                      className={`rounded-lg border px-3 transition ${
                        isDark
                          ? 'border-slate-700 text-slate-400 hover:border-rose-500 hover:text-rose-300'
                          : 'border-slate-300 text-slate-700 hover:border-rose-500 hover:text-rose-600'
                      }`}
                      aria-label="Odstranit člen jmenovatele"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={() => setTDen([...T_den, ''])}
                className={`text-[11px] font-semibold transition ${isDark ? 'text-sky-400 hover:text-sky-300' : 'text-sky-700 hover:text-sky-600'}`}
              >
                + Přidat člen
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className={`rounded-xl p-3 ${isDark ? 'border border-slate-800/80 bg-slate-950/50' : 'border border-slate-200 bg-slate-50'}`}>
              <div className="flex items-center justify-between">
                <label className={labelStyle}>Diferenciátor (s^m)</label>
                <button
                  type="button"
                  onClick={() => setDiffOrder(diffOrder === '' ? '1' : '')}
                  className={`rounded-lg border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider transition ${
                    isDark
                      ? 'border-slate-700 text-slate-400 hover:border-sky-500 hover:text-sky-300'
                      : 'border-slate-300 text-slate-700 hover:border-sky-500 hover:text-sky-700'
                  }`}
                >
                  {diffOrder === '' ? 'Přidat' : 'Odebrat'}
                </button>
              </div>
              {diffOrder !== '' && (
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={diffOrder}
                  onChange={(e) => setDiffOrder(e.target.value)}
                  className={inputStyle}
                />
              )}
            </div>

            <div className={`rounded-xl p-3 ${isDark ? 'border border-slate-800/80 bg-slate-950/50' : 'border border-slate-200 bg-slate-50'}`}>
              <div className="flex items-center justify-between">
                <label className={labelStyle}>Integrator (s^r)</label>
                <button
                  type="button"
                  onClick={() => setIntOrder(intOrder === '' ? '1' : '')}
                  className={`rounded-lg border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider transition ${
                    isDark
                      ? 'border-slate-700 text-slate-400 hover:border-amber-500 hover:text-amber-300'
                      : 'border-slate-300 text-slate-700 hover:border-amber-500 hover:text-amber-700'
                  }`}
                >
                  {intOrder === '' ? 'Přidat' : 'Odebrat'}
                </button>
              </div>
              {intOrder !== '' && (
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={intOrder}
                  onChange={(e) => setIntOrder(e.target.value)}
                  className={inputStyle}
                />
              )}
            </div>
          </div>
        </section>

        <section className={`rounded-2xl p-5 ${isDark ? 'border border-slate-700/50 bg-slate-900/40' : 'border border-slate-200 bg-white'}`}>
          <div className="mb-4 flex items-center gap-2">
            <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>Simulační scénář a porucha</h3>

            <div className="group relative">
              <button
                type="button"
                aria-label="Informace o simulaci"
                className={`flex h-4 w-4 items-center justify-center rounded-full border text-[10px] font-bold transition-colors focus:outline-none ${
                  isDark
                    ? 'border-slate-500 text-slate-500 hover:border-sky-400 hover:text-sky-400 focus:border-sky-400 focus:text-sky-400'
                    : 'border-slate-500 text-slate-500 hover:border-sky-500 hover:text-sky-700 focus:border-sky-500 focus:text-sky-700'
                }`}
              >
                i
              </button>

              <div
                className={`invisible absolute left-1/2 top-6 z-50 w-[min(20rem,calc(100vw-2rem))] -translate-x-1/2 rounded-xl p-4 opacity-0 shadow-2xl transition-all duration-200 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100 max-h-[70vh] overflow-y-auto ${
                  isDark ? 'border border-slate-700 bg-slate-800' : 'border border-slate-300 bg-white'
                }`}
              >
                <h4 className={`mb-3 border-b pb-1 text-xs font-bold uppercase ${isDark ? 'border-slate-700 text-sky-400' : 'border-slate-300 text-sky-700'}`}>Struktura simulace</h4>
                <div className={`space-y-3 text-[11px] leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  <section>
                    <span className={`font-bold ${isDark ? 'text-emerald-400' : 'text-emerald-700'}`}>Časové body (t1-t7):</span> Definují sekvenci změn žádané hodnoty (skoky a rampy).
                  </section>
                  <section>
                    <span className={`font-bold ${isDark ? 'text-emerald-400' : 'text-emerald-700'}`}>Amplitudy (w1, w2):</span> Úrovně, kterých má systém v daných časech dosáhnout.
                  </section>
                  <section className={`rounded border p-2 ${isDark ? 'border-amber-900/30 bg-slate-900/50' : 'border-amber-300 bg-amber-50'}`}>
                    <span className={`mb-1 block font-bold underline ${isDark ? 'text-amber-400' : 'text-amber-700'}`}>Externí porucha (td, d):</span>
                    <ul className="ml-3 list-disc space-y-1">
                      <li>
                        <span className={`font-semibold ${isDark ? 'text-white' : 'text-slate-800'}`}>td:</span> Čas, kdy do systému vstoupí porucha.
                      </li>
                      <li>
                        <span className={`font-semibold ${isDark ? 'text-white' : 'text-slate-800'}`}>d:</span> Velikost poruchy (přičítá se k akční veličině regulátoru). Testuje, jak se regulátor vyrovná s nárazem.
                      </li>
                    </ul>
                  </section>
                  <p className={`pt-1 text-[10px] italic ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Pozn: Metriky kvality (překmit, IAE) se počítají z prvního skoku v čase t1.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              {['t1', 't2', 't3', 't4', 't5', 't6', 't7', 'w1', 'w2', 'y0'].map((k) => (
                <div key={k}>
                  <input
                    type="number"
                    name={k}
                    value={k === 'y0' ? y0 : timeParams[k]}
                    onChange={k === 'y0' ? (e) => setY0(e.target.value) : handleTimeParamChange}
                    className={`${miniInputStyle} ${k === 'y0' ? (isDark ? 'border-emerald-700/50 text-emerald-300' : 'border-emerald-500/60 text-emerald-700') : (isDark ? 'text-slate-100' : 'text-slate-900')}`}
                  />
                  <div className={`mt-1 text-center text-[8px] font-medium uppercase ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>{k}</div>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
              <div className={`mb-2 text-center text-[10px] font-bold uppercase tracking-widest ${isDark ? 'text-amber-300/80' : 'text-amber-700'}`}>Nastavení poruchy</div>
              <div className="mx-auto flex max-w-xs justify-center gap-4">
                <div className="w-24">
                  <input type="number" name="td" value={timeParams.td} onChange={handleTimeParamChange} className={`${miniInputStyle} ${isDark ? 'border-amber-700/50 text-amber-200' : 'border-amber-400/60 text-amber-700'}`} />
                  <div className={`mt-1 text-center text-[8px] uppercase ${isDark ? 'text-amber-300/70' : 'text-amber-700'}`}>Čas (td)</div>
                </div>
                <div className="w-24">
                  <input type="number" name="d" value={timeParams.d} onChange={handleTimeParamChange} className={`${miniInputStyle} ${isDark ? 'border-amber-700/50 text-amber-200' : 'border-amber-400/60 text-amber-700'}`} />
                  <div className={`mt-1 text-center text-[8px] uppercase ${isDark ? 'text-amber-300/70' : 'text-amber-700'}`}>Velikost (d)</div>
                </div>
              </div>
            </div>
          </div>

          <div className={`mt-5 rounded-xl p-3 sm:p-4 ${isDark ? 'border border-slate-800 bg-slate-950/70 text-blue-100' : 'border border-slate-200 bg-slate-50 text-slate-800'}`}>
            <div className="overflow-x-auto">
              <div className="min-w-max pr-1">
                <BlockMath math={renderLatex()} />
              </div>
            </div>
          </div>
        </section>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className={`relative flex w-full items-center justify-center rounded-xl bg-sky-600 py-4 text-sm font-black uppercase tracking-[0.18em] text-white transition hover:bg-sky-500 disabled:cursor-not-allowed ${
          isDark ? 'shadow-lg shadow-sky-950/30 disabled:bg-slate-700' : 'shadow-lg shadow-sky-700/20 disabled:bg-slate-400'
        }`}
      >
        {isSubmitting && <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />}
        Analyzovat a vypočítat
      </button>
      {error && <p className={`text-center text-xs ${isDark ? 'text-rose-400' : 'text-rose-600'}`}>{error}</p>}
    </form>
  );
}

export default TransferFunctionInput;

