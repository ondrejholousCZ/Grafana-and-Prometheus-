#!/usr/bin/env python3
"""Stáhne dashboardy z grafana.com a připraví je pro file provisioning."""
import json
import os
import sys
import urllib.request

# (ID na grafana.com, složka v Grafaně, název souboru)
DASHBOARDS = [
    (1860,  "Linux",      "node-exporter-full.json"),
    (14694, "Windows",    "windows-exporter.json"),
    (14282, "Docker",     "cadvisor.json"),
    (7587,  "Monitoring", "blackbox-exporter.json"),
    (3662,  "Monitoring", "prometheus-overview.json"),
    (9578,  "Monitoring", "alertmanager.json"),
]

DS_UIDS = {"prometheus": "prometheus", "alertmanager": "alertmanager"}

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "grafana", "dashboards")
failed = []

for dash_id, folder, filename in DASHBOARDS:
    url = f"https://grafana.com/api/dashboards/{dash_id}/revisions/latest/download"
    req = urllib.request.Request(url, headers={"User-Agent": "monitoring-setup/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        data = json.loads(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[CHYBA] {dash_id}: {exc}")
        failed.append(dash_id)
        continue

    for inp in data.get("__inputs", []):
        if inp.get("type") == "datasource":
            uid = DS_UIDS.get(inp.get("pluginId"), "prometheus")
            text = text.replace("${" + inp["name"] + "}", uid)

    data = json.loads(text)
    data.pop("__inputs", None)
    data["id"] = None

    out_dir = os.path.join(BASE, folder)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"[OK] {dash_id} -> {folder}/{filename}  ({data.get('title')})")

if failed:
    print(f"Nepodařilo se stáhnout: {failed}")
    sys.exit(1)
