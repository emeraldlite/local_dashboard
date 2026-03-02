from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
import os

from tb_api import get_history, get_latest


APP_DIR = Path(__file__).resolve().parent
DEVICES_PATH = APP_DIR / "devices.json"

TELEMETRY_KEYS = ["level_pct", "weight_kg", "status", "status_code", "battery_v", "rssi_dbm"]
CHART_KEYS = ["level_pct", "weight_kg"]


def load_settings() -> tuple[str, str, int]:
    load_dotenv(APP_DIR / ".env")
    base_url = os.getenv("TB_BASE_URL", "https://eu.thingsboard.cloud")
    api_key = os.getenv("TB_API_KEY", "")
    refresh_sec = int(os.getenv("REFRESH_SEC", "5"))
    return base_url, api_key, refresh_sec


def load_devices() -> dict[str, str]:
    if not DEVICES_PATH.exists():
        st.error(
            "Missing local_dashboard/devices.json. Copy local_dashboard/devices.example.json to "
            "local_dashboard/devices.json and fill in your device UUIDs."
        )
        st.stop()
    with DEVICES_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("devices", {})


def fmt_ts(ts_ms: int | None) -> str:
    if ts_ms is None:
        return "-"
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def to_numeric(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def main() -> None:
    st.set_page_config(page_title="ThingsBoard Local Dashboard", layout="wide")
    st.title("ThingsBoard Cloud EU Telemetry Dashboard")

    base_url, api_key, default_refresh = load_settings()
    devices = load_devices()

    if not api_key:
        st.error("TB_API_KEY is not configured. Add it to local_dashboard/.env.")
        st.stop()

    bins = list(devices.keys())
    if not bins:
        st.error("No devices found in local_dashboard/devices.json")
        st.stop()

    with st.sidebar:
        selected_bin = st.selectbox("Choose bin", bins, index=0)
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_sec = st.number_input("Refresh interval (sec)", min_value=1, value=default_refresh, step=1)

    st.subheader("Latest values (A-01 to A-05)")
    rows = []
    for bin_name, device_id in devices.items():
        try:
            latest = get_latest(base_url, api_key, device_id, TELEMETRY_KEYS)
            row = {"bin": bin_name}
            last_seen_candidates = []
            for key in TELEMETRY_KEYS:
                row[key] = latest[key]["value"]
                if latest[key]["ts"] is not None:
                    last_seen_candidates.append(latest[key]["ts"])
            row["last_seen"] = fmt_ts(max(last_seen_candidates) if last_seen_candidates else None)
        except Exception as exc:  # noqa: BLE001
            row = {
                "bin": bin_name,
                "level_pct": None,
                "weight_kg": None,
                "status": f"error: {exc}",
                "status_code": None,
                "battery_v": None,
                "rssi_dbm": None,
                "last_seen": "-",
            }
        rows.append(row)

    latest_df = pd.DataFrame(rows).sort_values("bin")
    st.dataframe(latest_df, use_container_width=True)

    st.subheader(f"Last 15 minutes - {selected_bin}")
    end_ts = datetime.now(tz=timezone.utc)
    start_ts = end_ts - timedelta(minutes=15)

    selected_device_id = devices[selected_bin]
    history = get_history(
        base_url,
        api_key,
        selected_device_id,
        CHART_KEYS,
        int(start_ts.timestamp() * 1000),
        int(end_ts.timestamp() * 1000),
    )

    points = []
    for key in CHART_KEYS:
        for sample in history.get(key, []):
            if sample["ts"] is None:
                continue
            points.append(
                {
                    "time": datetime.fromtimestamp(sample["ts"] / 1000, tz=timezone.utc),
                    "metric": key,
                    "value": to_numeric(sample["value"]),
                }
            )

    chart_df = pd.DataFrame(points).dropna(subset=["value"])
    if chart_df.empty:
        st.info("No telemetry samples available in the selected range.")
    else:
        fig = px.line(chart_df, x="time", y="value", color="metric", markers=True)
        fig.update_layout(xaxis_title="Time (UTC)", yaxis_title="Value", legend_title="Metric")
        st.plotly_chart(fig, use_container_width=True)

    if auto_refresh:
        time.sleep(int(refresh_sec))
        st.rerun()


if __name__ == "__main__":
    main()
