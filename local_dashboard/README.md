# Local Dashboard

Simple Streamlit dashboard for ThingsBoard Cloud EU telemetry.

## Setup

1. Install dependencies:
   ```bash
   pip install -r local_dashboard/requirements.txt
   ```
2. Create environment file:
   ```bash
   copy local_dashboard\.env.example local_dashboard\.env
   ```
   Then set `TB_API_KEY` (and optionally `TB_BASE_URL`, `REFRESH_SEC`).
3. Create devices mapping:
   ```bash
   copy local_dashboard\devices.example.json local_dashboard\devices.json
   ```
   Then replace each device ID placeholder with the actual ThingsBoard device UUID.

## Run

```bash
streamlit run local_dashboard/app.py
```
