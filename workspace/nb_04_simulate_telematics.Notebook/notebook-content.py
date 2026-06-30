# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "language_info": {
# META     "name": "python"
# META   }
# META }

# MARKDOWN ********************

# # nb_04 — Simulate live telematics ➜ Eventhouse (optional)
#
# Generates a fresh batch of **vehicle telematics** events (usage-based-insurance signal)
# and streams them into the `kqldb_insurance_realtime` KQL database table `VehicleTelematics`.
#
# This is an **optional** realtime path. The primary live feed for the demo is the
# `es_telematics` Eventstream (built-in **SampleData** source — no external dependency).
# All endpoint URIs are resolved at runtime from the Fabric REST API; nothing is hardcoded.

# CELL ********************

%pip install azure-kusto-data azure-kusto-ingest --quiet

# CELL ********************

import random, datetime as dt, uuid
import pandas as pd
import requests
import notebookutils

KQL_DB_NAME = "kqldb_insurance_realtime"
EVENTHOUSE_NAME = "eh_insurance_realtime"
WORKSPACE_ID = notebookutils.runtime.context["currentWorkspaceId"]

# ---- Generate a batch of "live" telematics events -----------------------------
random.seed()
now = dt.datetime.utcnow()
rows = []
for i in range(2000):
    rows.append({
        "DeviceId": f"DEV{random.randint(100000, 999999)}",
        "PolicyId": f"PO{random.randint(1, 3000):07d}",
        "EventTime": (now - dt.timedelta(seconds=random.randint(0, 3600))).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SpeedMph": round(random.uniform(0, 90), 1),
        "HarshBrake": random.random() < 0.08,
        "HarshAccel": random.random() < 0.07,
        "Latitude": round(random.uniform(25.0, 48.0), 5),
        "Longitude": round(random.uniform(-123.0, -71.0), 5),
        "TripMiles": round(random.uniform(0.5, 40.0), 2),
    })
pdf = pd.DataFrame(rows)
print(f"Generated {len(pdf)} telematics events")

# CELL ********************

# ---- Resolve the Eventhouse query URI from the Fabric REST API ----------------
fabric_token = notebookutils.credentials.getToken("pbi")
headers = {"Authorization": f"Bearer {fabric_token}"}

def resolve_query_uri():
    base = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/eventhouses"
    items = requests.get(base, headers=headers).json().get("value", [])
    eh = next((e for e in items if e["displayName"] == EVENTHOUSE_NAME), None)
    if not eh:
        raise RuntimeError(f"Eventhouse '{EVENTHOUSE_NAME}' not found in workspace.")
    detail = requests.get(f"{base}/{eh['id']}", headers=headers).json()
    return detail["properties"]["queryServiceUri"]

# CELL ********************

# ---- Stream the batch into the KQL table (best effort) ------------------------
try:
    from azure.kusto.data import KustoConnectionStringBuilder
    from azure.kusto.data.data_format import DataFormat
    from azure.kusto.ingest import KustoStreamingIngestClient, IngestionProperties

    query_uri = resolve_query_uri()
    kcsb = KustoConnectionStringBuilder.with_token_provider(
        query_uri, lambda: notebookutils.credentials.getToken("kusto"))
    client = KustoStreamingIngestClient(kcsb)
    props = IngestionProperties(database=KQL_DB_NAME, table="VehicleTelematics",
                                data_format=DataFormat.CSV)
    client.ingest_from_dataframe(pdf, ingestion_properties=props)
    msg = f"Ingested {len(pdf)} rows into {KQL_DB_NAME}.VehicleTelematics"
    print(msg)
except Exception as e:
    msg = (f"Streaming ingest skipped: {e}. "
           f"Ensure the Eventhouse exists and you have 'Table ingestor' rights, "
           f"or use the es_telematics Eventstream SampleData source instead.")
    print(msg)

notebookutils.notebook.exit(msg)
