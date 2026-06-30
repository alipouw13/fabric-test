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

# # nb_00 — Generate Contoso Insurance demo data
#
# Synthesizes a cohesive **property & casualty insurance** dataset entirely in-notebook
# (no external sources) and lands it in the **bronze** schema of `lh_insurance`.
#
# Entities: `agents`, `customers`, `policies`, `claims`, `premium_transactions`, `vehicle_telematics`.
#
# The lakehouse is resolved **at runtime by name** so no GUIDs are hardcoded.

# CELL ********************

import random
import datetime as dt
import pandas as pd
import notebookutils

# Deterministic demo data
random.seed(42)

# Resolve the lakehouse by NAME at runtime (no hardcoded GUIDs)
LAKEHOUSE_NAME = "lh_insurance"
WORKSPACE_ID = notebookutils.runtime.context["currentWorkspaceId"]
LAKEHOUSE_ID = notebookutils.lakehouse.get(LAKEHOUSE_NAME)["id"]
TABLES_BASE = f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}/Tables"

def write_delta(pdf, schema, table):
    """Write a pandas DataFrame as a Delta table under Tables/<schema>/<table>."""
    sdf = spark.createDataFrame(pdf)
    (sdf.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(f"{TABLES_BASE}/{schema}/{table}"))
    return sdf.count()

print(f"Workspace: {WORKSPACE_ID}")
print(f"Lakehouse: {LAKEHOUSE_NAME} ({LAKEHOUSE_ID})")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ---- Reference data ------------------------------------------------------------
STATES = ["WA", "CA", "TX", "NY", "FL", "IL", "CO", "GA", "AZ", "MA"]
CITIES = {
    "WA": "Seattle", "CA": "Los Angeles", "TX": "Austin", "NY": "New York",
    "FL": "Miami", "IL": "Chicago", "CO": "Denver", "GA": "Atlanta",
    "AZ": "Phoenix", "MA": "Boston",
}
POLICY_TYPES = ["Auto", "Home", "Life", "Umbrella"]
CHANNELS = ["Direct", "Agent", "Broker", "Online"]
CREDIT_TIERS = ["Excellent", "Good", "Fair", "Poor"]
LOSS_TYPES = {
    "Auto": ["Collision", "Comprehensive", "Liability", "Theft"],
    "Home": ["Fire", "Water", "Wind", "Theft", "Liability"],
    "Life": ["Death Benefit"],
    "Umbrella": ["Excess Liability"],
}
FIRST = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
         "Linda", "David", "Elizabeth", "Maria", "Wei", "Aarav", "Sofia", "Omar"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Chen", "Patel", "Kim", "Nguyen", "Ali"]

def rand_date(start_year=2018, end_year=2024):
    start = dt.date(start_year, 1, 1)
    end = dt.date(end_year, 12, 31)
    return start + dt.timedelta(days=random.randint(0, (end - start).days))

# ---- Agents --------------------------------------------------------------------
N_AGENTS = 50
agents = []
for i in range(1, N_AGENTS + 1):
    st = random.choice(STATES)
    agents.append({
        "agent_id": f"AG{i:04d}",
        "agent_name": f"{random.choice(FIRST)} {random.choice(LAST)}",
        "region": st,
        "channel": random.choice(CHANNELS),
        "hire_date": rand_date(2010, 2023),
    })
agents_pdf = pd.DataFrame(agents)

# ---- Customers -----------------------------------------------------------------
N_CUSTOMERS = 2000
customers = []
for i in range(1, N_CUSTOMERS + 1):
    st = random.choice(STATES)
    fn, ln = random.choice(FIRST), random.choice(LAST)
    customers.append({
        "customer_id": f"CU{i:06d}",
        "first_name": fn,
        "last_name": ln,
        "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
        "date_of_birth": rand_date(1955, 2003),
        "gender": random.choice(["F", "M", "X"]),
        "city": CITIES[st],
        "state": st,
        "postal_code": f"{random.randint(10000, 99999)}",
        "credit_tier": random.choices(CREDIT_TIERS, weights=[3, 4, 2, 1])[0],
        "customer_since": rand_date(2012, 2024),
    })
customers_pdf = pd.DataFrame(customers)

print(f"agents={len(agents_pdf)}  customers={len(customers_pdf)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ---- Policies ------------------------------------------------------------------
N_POLICIES = 3000
policies = []
customer_ids = customers_pdf["customer_id"].tolist()
agent_ids = agents_pdf["agent_id"].tolist()
for i in range(1, N_POLICIES + 1):
    ptype = random.choices(POLICY_TYPES, weights=[5, 4, 2, 1])[0]
    start = rand_date(2020, 2024)
    term_months = random.choice([6, 12])
    end = start + dt.timedelta(days=term_months * 30)
    base_premium = {"Auto": 1200, "Home": 1600, "Life": 800, "Umbrella": 400}[ptype]
    premium = round(base_premium * random.uniform(0.6, 1.8), 2)
    policies.append({
        "policy_id": f"PO{i:07d}",
        "customer_id": random.choice(customer_ids),
        "agent_id": random.choice(agent_ids),
        "policy_type": ptype,
        "product": f"{ptype} {random.choice(['Standard', 'Premier', 'Essential'])}",
        "start_date": start,
        "end_date": end,
        "term_months": term_months,
        "status": random.choices(["Active", "Lapsed", "Cancelled"], weights=[8, 1, 1])[0],
        "annual_premium": premium,
        "deductible": random.choice([250, 500, 1000, 2500]),
        "coverage_limit": random.choice([50000, 100000, 250000, 500000, 1000000]),
    })
policies_pdf = pd.DataFrame(policies)
print(f"policies={len(policies_pdf)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ---- Claims + Premium transactions + Telematics seed --------------------------
policy_rows = policies_pdf.to_dict("records")

# Claims (~50% of policies generate at least one claim)
claims = []
cidx = 1
for p in policy_rows:
    for _ in range(random.choices([0, 1, 2, 3], weights=[50, 30, 15, 5])[0]):
        reported = round(random.uniform(500, p["coverage_limit"] * 0.4), 2)
        status = random.choices(["Open", "Closed", "Denied"], weights=[3, 6, 1])[0]
        paid = 0.0 if status == "Denied" else round(reported * random.uniform(0.3, 1.0), 2)
        claims.append({
            "claim_id": f"CL{cidx:08d}",
            "policy_id": p["policy_id"],
            "customer_id": p["customer_id"],
            "claim_date": p["start_date"] + dt.timedelta(days=random.randint(1, 330)),
            "loss_type": random.choice(LOSS_TYPES[p["policy_type"]]),
            "claim_status": status,
            "reported_amount": reported,
            "paid_amount": paid,
            "fraud_flag": random.random() < 0.04,
            "catastrophe_flag": random.random() < 0.06,
        })
        cidx += 1
claims_pdf = pd.DataFrame(claims)

# Premium transactions (monthly installments for the policy term)
txns = []
tidx = 1
for p in policy_rows:
    installments = p["term_months"]
    monthly = round(p["annual_premium"] * (p["term_months"] / 12.0) / installments, 2)
    for m in range(installments):
        txns.append({
            "txn_id": f"TX{tidx:09d}",
            "policy_id": p["policy_id"],
            "txn_date": p["start_date"] + dt.timedelta(days=30 * m),
            "amount": monthly,
            "payment_method": random.choice(["Card", "ACH", "Check", "Wallet"]),
            "billing_period": f"{p['start_date'].year}-{((p['start_date'].month + m - 1) % 12) + 1:02d}",
        })
        tidx += 1
txns_pdf = pd.DataFrame(txns)

# Vehicle telematics seed (Auto policies only) — also feeds the real-time demo
auto_policies = [p for p in policy_rows if p["policy_type"] == "Auto"][:300]
telematics = []
base_ts = dt.datetime(2024, 1, 15, 8, 0, 0)
for p in auto_policies:
    for s in range(random.randint(5, 20)):
        telematics.append({
            "device_id": f"DEV{p['policy_id'][-6:]}",
            "policy_id": p["policy_id"],
            "event_time": base_ts + dt.timedelta(minutes=random.randint(0, 20000)),
            "speed_mph": round(random.uniform(0, 85), 1),
            "harsh_brake": random.random() < 0.08,
            "harsh_accel": random.random() < 0.07,
            "latitude": round(random.uniform(25.0, 48.0), 5),
            "longitude": round(random.uniform(-123.0, -71.0), 5),
            "trip_miles": round(random.uniform(0.5, 40.0), 2),
        })
telematics_pdf = pd.DataFrame(telematics)

print(f"claims={len(claims_pdf)}  txns={len(txns_pdf)}  telematics={len(telematics_pdf)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ---- Land everything in the BRONZE schema as Delta tables ----------------------
counts = {
    "agents": write_delta(agents_pdf, "bronze", "agents"),
    "customers": write_delta(customers_pdf, "bronze", "customers"),
    "policies": write_delta(policies_pdf, "bronze", "policies"),
    "claims": write_delta(claims_pdf, "bronze", "claims"),
    "premium_transactions": write_delta(txns_pdf, "bronze", "premium_transactions"),
    "vehicle_telematics": write_delta(telematics_pdf, "bronze", "vehicle_telematics"),
}
for t, c in counts.items():
    print(f"bronze.{t:<22} rows={c}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Return a summary to the pipeline / caller
notebookutils.notebook.exit(str(counts))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
