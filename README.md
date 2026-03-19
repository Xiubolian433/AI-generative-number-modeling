# 🎰 LotteryGenAI Generator
A generative AI-based lottery number generator powered by GAN models and integrated into a full-stack web platform built with React, Flask, SQLite, and PayPal.

⚠️ Disclaimer: This project is for entertainment purposes only. Generated numbers are not guaranteed to increase your chances of winning. Please play responsibly.

Current production deployment:

- Frontend: custom domain on Render Static Site
- Backend: Render Python Web Service
- Database: SQLite on a Render Persistent Disk

# Project Overview
LotteryGenAI is a web-based application that uses trained generative models to analyze historical lottery results and generate statistically plausible combinations for:

- Mega Millions
- Powerball

The platform currently includes:

- 🎲 AI-powered lottery number generation
- 💰 PayPal sandbox/live payment support with credit packages
- 🔑 Access-code based credit recovery across devices
- 📊 Automatically refreshed History Numbers and History Statistic pages
- ⚡ Cached official history data for faster production performance
- 📱 Responsive layouts tuned for desktop, iPad, iPhone, and foldable-width devices
- 🌐 React frontend and Flask backend
- 💾 Local SQLite persistence for payments and credits

# 📁 Project Structure
```bash
lotteryGenAI/
├── frontend/                    # React-based frontend UI
│   ├── public/
│   └── src/
│       ├── components/          # History, payment, intro views
│       ├── App.js               # Main app shell and routing
│       ├── Generator.js         # Mega Millions generator page
│       ├── powerball_generator.js
│       ├── api.js               # Frontend API client
│       └── credits.js           # Shared credit state helpers
├── backend/
│   ├── Flask_app_simplified.py  # Active backend entrypoint
│   ├── official_history_api.py  # Official-source history fetch + stats
│   ├── gan_generator.py         # Mega Millions model definition
│   ├── gan_power_generator.py   # Powerball model definition
│   ├── database_config.py
│   ├── database_models.py
│   ├── database_service.py
│   ├── gan_generator.pth
│   ├── gan_powerball_generator.pth
│   ├── payments.db              # Local SQLite database
│   └── .env.example             # Backend environment template
├── render.yaml                  # Render blueprint for frontend + backend
├── Dockerfile                   # Optional Railway backend container build
├── railway.json                 # Optional Railway deployment settings
├── Lottery_data/                # Historical lottery datasets
├── requirements.txt             # Python dependencies
└── README.md
```

# 🧠 AI & GAN Model
The backend uses custom-trained GAN models (`gan_generator.pth`, `gan_powerball_generator.pth`) to:

- Learn from historical lottery datasets
- Generate statistically plausible number combinations
- Support different lottery types: Mega Millions and Powerball

# 🚀 Features
### ✅ AI-Powered Number Generation
Generate Mega Millions and Powerball combinations using trained models.

### 📊 Auto-Updated Lottery History
`History Numbers` and `History Statistic` now use official public lottery sources instead of the old third-party RapidAPI wrappers.

- Mega Millions history is fetched from the official Mega Millions site
- Powerball history is fetched from the official Powerball site
- Statistics are computed locally from the latest fetched draw history
- Production now caches fetched history data to reduce latency and improve reliability on hosted environments

### 💳 PayPal Credit Purchase Flow
Users can purchase credits through PayPal and use them immediately after successful payment.

Available packages:

- `$1` → `5` credits
- `$5` → `30` credits
- `$10` → `70` credits
- `$20` → `150` credits

### 🔑 Access Code Recovery
Each completed payment is tied to an access code so paid credits can be restored on another device.

### 💾 Persistent Credits & Payments
The app stores:

- Payment records
- Access codes
- Remaining credits
- Used credits

using a local SQLite database (`backend/payments.db`).

### 📱 Responsive UI
The current frontend has been tuned for:

- Desktop and large laptop layouts
- iPad and tablet widths
- iPhone portrait layouts
- Narrow Android / foldable device widths

Special attention has been given to:

- homepage hero layout
- generator pages
- History Numbers and History Statistic pages
- payment success and top-up flows

# Current Architecture
The currently active backend entrypoint is:

```bash
backend/Flask_app_simplified.py
```

This file is responsible for:

- model loading
- generation APIs
- payment creation and execution
- credit verification and consumption
- health checks
- history numbers/statistics routes

# Installation and Running
## 1. Clone the repository
```bash
git clone https://github.com/yourusername/lotteryGenAI.git
cd lotteryGenAI
```

## 2. Backend Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
cp .env.example .env
PORT=5050 python Flask_app_simplified.py
```

Default local backend:

```bash
http://127.0.0.1:5050
```

## 3. Frontend Setup
Open a second terminal:

```bash
cd /path/to/lotteryGenAI
source .venv/bin/activate
cd frontend
yarn install
yarn start
```

Default local frontend:

```bash
http://localhost:3000
```

# 🔧 Environment Configuration
## Backend `.env`
Create:

```bash
backend/.env
```

Example:

```env
PORT=5050
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://127.0.0.1:5050
PAYMENTS_DB_PATH=payments.db

PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
```

Note:

- `PAYPAL_MODE` can be `sandbox` or `live`.
- `PAYMENTS_DB_PATH` defaults to `payments.db` locally.
- On Render, set `PAYMENTS_DB_PATH=/var/data/payments.db` and attach a persistent disk mounted at `/var/data`.

## Frontend `.env.local`
Create:

```bash
frontend/.env.local
```

Example:

```env
REACT_APP_API_BASE_URL=http://127.0.0.1:5050
```

# 💳 Payment Flow
The current payment flow is:

1. The user clicks `Top Up`
2. The frontend requests `/api/payment/create-order`
3. The backend creates a PayPal payment and stores a pending record in SQLite
4. The user completes PayPal approval
5. The frontend returns to `/payment/success`
6. The frontend calls `/api/payment/execute`
7. The backend marks the payment as completed and adds credits
8. The frontend stores the access code and updates visible credit state

# 📊 History Data Flow
The current history flow is:

1. The frontend requests `History Numbers` or `History Statistic`
2. The backend fetches the latest official draw history
3. The backend caches the results for a short period
4. `History Statistic` is computed locally from fetched draw data

This means the history pages update automatically without requiring manual CSV refreshes.

# Frequently Asked Questions and Solutions
## 1. DNS and CORS misconfiguration caused frontend requests to fail.

Problem Description:
During deployment, the front-end and back-end may use different domains. If the backend CORS configuration is incorrect, frontend requests can be blocked even when the application itself is healthy.

Incorrect pattern:
```python
CORS(app, resources={
    r"/*": {
        "origins": [FRONTEND_URL],  # Nested list problem
    }
})
```

Correct pattern:
```python
CORS(app, resources={
    r"/*": {
        "origins": FRONTEND_URL,
    }
})
```

## 2. Inconsistent frontend and backend URLs caused the page to fail in deployment.

Problem Description:
Hardcoded local URLs such as `http://localhost:5000` often work in development, but break in production or custom environments.

Solution:

Use environment variables consistently.

Frontend:
```javascript
const baseURL = process.env.REACT_APP_API_BASE_URL;
```

Backend:
```python
BACKEND_URL = os.getenv("BACKEND_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
```

### In summary
All frontend routes and API addresses should be managed through environment variables rather than hardcoded local values.

# ☁️ Deployment
The recommended deployment setup for the current version of this project is:

- Frontend: `Render Static Site`
- Backend: `Render Python Web Service`
- Database: SQLite stored on a `Render Persistent Disk`

The repository includes [render.yaml](/Users/shuhaozhang/Documents/AI-generative-number-modeling/render.yaml) so the stack can be created from a Render Blueprint.

## Render backend
Recommended backend settings:

- Runtime: `Python`
- Python version: `3.11` (the repository includes `runtime.txt` and `.python-version` for Render compatibility with PyTorch)
- Plan: `Starter` or higher
- Start command: `gunicorn --chdir backend --bind 0.0.0.0:$PORT --worker-class gthread --threads 4 --workers 1 --timeout 300 Flask_app_simplified:app`
- Health check path: `/api/health`

Recommended backend environment values:

```env
FRONTEND_URL=https://lotteryganai.com
BACKEND_URL=https://your-render-backend.onrender.com
PAYMENTS_DB_PATH=/var/data/payments.db

PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
```

Recommended persistent disk:

- Mount path: `/var/data`

## Render frontend
Recommended frontend settings:

- Runtime: `Static Site`
- Root directory: `frontend`
- Build command: `yarn install && yarn build`
- Publish directory: `build`

Frontend environment variable:

```env
REACT_APP_API_BASE_URL=https://your-render-backend.onrender.com
```

Note:

- [render.yaml](/Users/shuhaozhang/Documents/AI-generative-number-modeling/render.yaml) includes a catch-all rewrite so React Router routes such as `/history-numbers` and `/payment/success` load correctly.
- A simple production setup is to use a custom domain only for the frontend and keep the backend on its Render-generated domain.
- If you use Render-generated domains first, update `FRONTEND_URL`, `BACKEND_URL`, and `REACT_APP_API_BASE_URL` after custom domains are connected.

# 🌍 Environment Differentiation and Configuration Management
To ensure consistent behavior between local development and deployment, the project uses environment files.

## Local development example
```env
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://127.0.0.1:5050
PAYPAL_MODE=sandbox
```

## Production example
```env
FRONTEND_URL=https://lotteryganai.com
BACKEND_URL=https://your-render-backend.onrender.com
PAYMENTS_DB_PATH=/var/data/payments.db
PAYPAL_MODE=sandbox
```

# 💸 Estimated Monthly Cost
Based on the current production setup used for this project:

- Render Static Site: `$0/month`
- Render Starter Web Service: `$7/month`
- Render Persistent Disk (1 GB): `$0.25/month`
- Namecheap `.com` renewal: about `$18.48/year`
- ICANN fee: `$0.20/year`

Approximate monthly operating cost:

- Render only: about `$7.25/month`
- Domain averaged monthly: about `$1.56/month`
- Total average monthly cost: about `$8.81/month`

This estimate assumes:

- one `Starter` backend service
- one `1 GB` persistent disk
- one frontend static site
- one `.com` domain renewed yearly at current public pricing

If traffic stays within Render Hobby plan bandwidth allowances and you do not add extra services, this is a reasonable baseline for day-to-day maintenance.

# Health Check
Once the backend is running, verify it with:

```bash
curl http://127.0.0.1:5050/api/health
```

Expected indicators include:

- backend reachable
- database present
- PayPal configuration status
- active frontend/backend URLs

# Notes for GitHub
- Do not commit real PayPal credentials or other secrets
- Keep `backend/.env` local only
- Commit only placeholder values in `backend/.env.example`

# Production Notes
- The frontend can run on a custom root domain such as `lotteryganai.com`
- The backend can remain on a Render-generated domain if you do not need a separate public API domain
- SQLite production data is stored on the Render persistent disk at `/var/data/payments.db`
- Official lottery history pages are cached on the backend to improve first-load performance and reduce external request failures

# License / Usage Notice
This repository is intended for educational and entertainment purposes. Users are responsible for complying with all applicable laws, platform rules, and payment provider terms.
