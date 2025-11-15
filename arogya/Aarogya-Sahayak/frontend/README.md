# Arogya Sahayak — Frontend

Modern Vite + React frontend for the Arogya Sahayak backend.

Run locally

PowerShell (Windows):

```
cd d:/iccx/arogya/Aarogya-Sahayak/frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000` (see `vite.config.js`).

Usage

- Open `http://localhost:5173` in your browser.
- Click **Use my location** to attach lat/lon to requests (optional).
- Ask a medical question and press Enter or click Send.

Notes

- This frontend expects the backend to be running on `http://localhost:8000` and exposes backend endpoints under `/api/*`.
- I did not modify backend code per request.
