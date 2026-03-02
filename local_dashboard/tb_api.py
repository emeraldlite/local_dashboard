from __future__ import annotations

from typing import Any

import requests


def make_headers(api_key: str) -> dict[str, str]:
    return {"X-Authorization": f"ApiKey {api_key}"}


def get_latest(base_url: str, api_key: str, device_id: str, keys: list[str]) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
    params = {"keys": ",".join(keys)}
    response = requests.get(url, headers=make_headers(api_key), params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()

    latest: dict[str, Any] = {}
    for key in keys:
        series = payload.get(key, [])
        if series:
            point = series[0]
            latest[key] = {
                "ts": int(point.get("ts")) if point.get("ts") is not None else None,
                "value": point.get("value"),
            }
        else:
            latest[key] = {"ts": None, "value": None}
    return latest


def get_history(
    base_url: str,
    api_key: str,
    device_id: str,
    keys: list[str],
    start_ts_ms: int,
    end_ts_ms: int,
) -> dict[str, list[dict[str, Any]]]:
    url = f"{base_url.rstrip('/')}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
    params = {
        "keys": ",".join(keys),
        "startTs": start_ts_ms,
        "endTs": end_ts_ms,
        "agg": "NONE",
        "limit": 200,
    }
    response = requests.get(url, headers=make_headers(api_key), params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()

    history: dict[str, list[dict[str, Any]]] = {}
    for key in keys:
        data = payload.get(key, [])
        history[key] = [
            {
                "ts": int(item.get("ts")) if item.get("ts") is not None else None,
                "value": item.get("value"),
            }
            for item in data
        ]
    return history
