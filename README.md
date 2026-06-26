# PIDtuner

A web application for calculating, tuning, and analyzing PID controllers. The project lets you define a plant transfer function, tune controller gains with several methods, check closed-loop stability, and inspect step responses and simulation results on charts.

## Features

- Transfer function input for `G(s)` using gain, numerator and denominator time constants, transport delay, differentiator terms, and integrator terms.
- Support for real values and complex-conjugate time constants.
- Gain calculation for `P`, `PI`, `PD`, and `PID` controllers.
- Tuning methods: Ziegler-Nichols, CHR, IMC/Lambda, and a genetic algorithm.
- Automatic FOPDT approximation for methods that require a first-order plus dead-time model.
- Closed-loop simulation with step/ramp setpoint scenarios and a constant input disturbance.
- Control quality metrics: overshoot, settling time, IAE, and ITAE.
- Continuous and discrete stability analysis with pole plots in the `s`-plane and `z`-plane.
- Dark/light theme and `CZ/EN` interface language switch.

## Tech Stack

**Backend**

- Python 3.11
- Flask
- NumPy, SciPy
- python-control
- Gunicorn for production

**Frontend**

- React 19
- Create React App
- Tailwind CSS
- Chart.js and react-chartjs-2
- KaTeX for formula rendering

## Project Structure

```text
.
|-- Backend/
|   |-- app.py                 # Flask API and main calculation endpoint
|   |-- requirements.txt       # Python dependencies
|   |-- Procfile               # Production backend start command
|   |-- GA.py                  # Genetic algorithm tuning
|   |-- IMC.py                 # IMC/Lambda tuning
|   |-- zn_method.py           # Ziegler-Nichols method
|   |-- CHR_*.py               # CHR methods
|   |-- Sim.py                 # Closed-loop simulation
|   `-- stability.py           # Stability analysis
|-- Frontend/
|   `-- pid-frontend/
|       |-- src/               # React UI components
|       |-- public/            # Static files
|       |-- package.json       # npm scripts and dependencies
|       `-- vercel.json        # SPA routing config for Vercel
`-- render.yaml                # Example backend config for Render
```

## Local Development

### 1. Backend

Go to the backend directory:

```powershell
cd Backend
```

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the Flask API:

```powershell
python app.py
```

By default, the backend runs at `http://127.0.0.1:5000`.

Health check:

```powershell
curl http://127.0.0.1:5000/health
```

Expected response:

```json
{"status":"ok"}
```

### 2. Frontend

In a new terminal, go to the frontend directory:

```powershell
cd Frontend\pid-frontend
```

Install dependencies:

```powershell
npm install
```

Start the app:

```powershell
npm start
```

The frontend will open at `http://localhost:3000`. In development mode, API requests are proxied to `http://127.0.0.1:5000` through the `proxy` field in `package.json`.

## Environment Variables

### Backend

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `5000` | Flask application port |
| `FLASK_DEBUG` | `0` | Enables debug mode when set to `1` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed CORS origins |

Example:

```powershell
$env:CORS_ALLOWED_ORIGINS="http://localhost:3000,https://your-frontend.vercel.app"
python app.py
```

### Frontend

| Variable | Description |
| --- | --- |
| `REACT_APP_API_URL` | Backend API base URL. If omitted, the frontend uses relative API paths such as `/calculate` |

Example `.env` for a production frontend build:

```env
REACT_APP_API_URL=https://your-backend.onrender.com
```

## API

### `GET /health`

Checks whether the backend is running.

### `POST /calculate`

Main endpoint for controller tuning, stability analysis, and simulation.

Minimal request example:

```json
{
  "K": "1",
  "T_num": [],
  "T_den": ["1"],
  "L": "1",
  "diffOrder": 0,
  "intOrder": 0,
  "Method": "ZN",
  "controllerType": "PID",
  "timeParams": [460, 860, 1260, 1660, 2060, 2460, 2500, 150, 170, 1200, 0],
  "y0": 70
}
```

For `Method: "GA"`, you can also pass:

```json
{
  "generations": 50,
  "population_size": 20,
  "mutation_rate": 0.1
}
```

For `Method: "IMC"`, you can pass:

```json
{
  "lambdaAlpha": 2
}
```

Supported `Method` values:

- `ZN`
- `GA`
- `IMC`
- `CHR_0_POZ_H`
- `CHR_20_POZ_H`
- `CHR_0_POT_P`
- `CHR_20_POT_P`

Supported `controllerType` values:

- `P`
- `PI`
- `PD`
- `PID`

## Frontend Build

```powershell
cd Frontend\pid-frontend
npm run build
```

The production build will be generated in `Frontend/pid-frontend/build`.

## Deployment

### Backend on Render

The root `render.yaml` file describes the backend service:

- `rootDir: Backend`
- dependency installation with `pip install -r requirements.txt`
- start command: `gunicorn app:app --workers 1 --timeout 600 --graceful-timeout 30`

Before deployment, set the real frontend URL in `CORS_ALLOWED_ORIGINS`.

### Frontend on Vercel

The frontend is located in `Frontend/pid-frontend`. The `vercel.json` file is used for SPA routing.

Add this environment variable in Vercel:

```env
REACT_APP_API_URL=https://your-backend-url
```

## Useful Commands

```powershell
# Backend
cd Backend
python app.py

# Frontend dev server
cd Frontend\pid-frontend
npm start

# Frontend production build
cd Frontend\pid-frontend
npm run build

# Frontend tests
cd Frontend\pid-frontend
npm test
```

## Notes

- Ziegler-Nichols and CHR methods require transport delay: `L > 0`.
- When using complex time constants, provide conjugate pairs so the resulting polynomial remains real.
- If the closed-loop system is unstable, the backend returns a stability report but does not run the full control-quality time simulation.
