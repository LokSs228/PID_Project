import React, { useState } from 'react';
import 'katex/dist/katex.min.css';
import { BlockMath } from 'react-katex';

function TransferFunctionInput({ onResult }) {
  const [K, setK] = useState('');
  const [T_num, setTNum] = useState(['']);
  const [T_den, setTDen] = useState(['']);
  const [L, setL] = useState('');
  const [method, setMethod] = useState('ZN');
  const [error, setError] = useState('');

  const [timeParams, setTimeParams] = useState({
    t1: 460, t2: 860, t3: 1260, t4: 1660, t5: 2060, t6: 2460, t7: 2500,
    w1: 150, w2: 170,
  });
  const [y0, setY0] = useState(70);

  const handleTimeParamChange = (e) => {
    const { name, value } = e.target;
    setTimeParams((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const numericTNum = T_num.map(val => parseFloat(val)).filter(val => !isNaN(val));
      const numericTDen = T_den.map(val => parseFloat(val)).filter(val => !isNaN(val));
      const timeParamsArray = Object.values(timeParams).map(parseFloat);

      const body = {
        K: parseFloat(K),
        T_num: numericTNum,
        T_den: numericTDen,
        Method: method,
        timeParams: timeParamsArray,
        y0: parseFloat(y0),
      };
      if (L !== '') body.L = parseFloat(L);

      const response = await fetch('/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Chyba při odesílání požadavku');
      onResult(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const renderLatex = () => {
    if (K === '' || T_den.length === 0 || T_den.some((t) => t === '')) {
      return 'Přenosová funkce bude zobrazena zde';
    }

    const numerator = T_num
      .filter((val) => val !== '')
      .map((val) => `(${val}s + 1)`)
      .join('\\cdot ');

    const denominator = T_den
      .filter((val) => val !== '')
      .map((val) => `(${val}s + 1)`)
      .join('\\cdot ');

    const delayPart = L !== '' ? `\\cdot e^{- ${L}s}` : '';

    return `\\frac{${K}${numerator ? '\\cdot ' + numerator : ''}}{${denominator}}${delayPart}`;
  };

  return (
    <div>
      <h2>Zadejte parametry přenosové funkce:</h2>
      <form onSubmit={handleSubmit}>
        <label>
          K:
          <input
            type="number"
            step="any"
            value={K}
            onChange={(e) => setK(e.target.value)}
            required
          />
        </label>

        <label>
          {' '}
          L (zpoždění):
          <input
            type="number"
            step="any"
            value={L}
            onChange={(e) => setL(e.target.value)}
          />
        </label>

        <h4>Čitatel (Tₙ): </h4>
        {T_num.map((value, index) => (
          <div key={index}>
            <input
              type="number"
              step="any"
              value={value}
              onChange={(e) => {
                const newT = [...T_num];
                newT[index] = e.target.value;
                setTNum(newT);
              }}
              placeholder={`Tnum${index + 1}`}
            />
            {T_num.length > 1 && (
              <button type="button" onClick={() => {
                setTNum(T_num.filter((_, i) => i !== index));
              }}>❌</button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => setTNum([...T_num, ''])}>➕ Přidat Tₙ</button>

        <h4>Jmenovatel (T_d):</h4>
        {T_den.map((value, index) => (
          <div key={index}>
            <input
              type="number"
              step="any"
              value={value}
              onChange={(e) => {
                const newT = [...T_den];
                newT[index] = e.target.value;
                setTDen(newT);
              }}
              placeholder={`Tden${index + 1}`}
            />
            {T_den.length > 1 && (
              <button type="button" onClick={() => {
                setTDen(T_den.filter((_, i) => i !== index));
              }}>❌</button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => setTDen([...T_den, ''])}>➕ Přidat Tₙ</button>

        <label>
          Metoda nastavení:
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            style={{ marginLeft: 10 }}
          >
            <option value="ZN">Ziegler–Nichols</option>
            <option value="GA">Genetic Algorithm</option>
          </select>
        </label>

        <hr style={{ margin: '20px 0' }} />

        <h3>Časové parametry a vstupní signály:</h3>
        {[
          't1', 't2', 't3', 't4', 't5', 't6', 't7', 'w1', 'w2'
        ].map((key) => (
          <div key={key}>
            <label>
              {key.toUpperCase()}:
              <input
                type="number"
                step="any"
                name={key}
                value={timeParams[key]}
                onChange={handleTimeParamChange}
                required
              />
            </label>
          </div>
        ))}

        <div>
          <label>
            Y₀ (počáteční hodnota):
            <input
              type="number"
              step="any"
              name="y0"
              value={y0}
              onChange={(e) => setY0(parseFloat(e.target.value))}
            />
          </label>
        </div>

        <br />
        <button type="submit">Vypočítat PID</button>
      </form>

      <div style={{ marginTop: 20 }}>
        <h3>Přenosová funkce:</h3>
        <BlockMath math={renderLatex()} />
      </div>

      {error && <p style={{ color: 'red' }}>Chyba: {error}</p>}
    </div>
  );
}

export default TransferFunctionInput;



