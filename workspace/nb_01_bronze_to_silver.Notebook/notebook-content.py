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

# # nb_01 — Bronze ➜ Silver
#
# Cleans and conforms raw bronze tables into curated **silver** Delta tables:
# type casting, de-duplication, derived columns (customer age, policy tenure,
# claim loss ratio inputs) and basic data-quality filters.

# CELL ********************

import notebookutils
from pyspark.sql import functions as F

LAKEHOUSE_NAME = "lh_insurance"
WORKSPACE_ID = notebookutils.runtime.context["currentWorkspaceId"]
LAKEHOUSE_ID = notebookutils.lakehouse.get(LAKEHOUSE_NAME)["id"]
TABLES_BASE = f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}/Tables"

def read_delta(schema, table):
    return spark.read.format("delta").load(f"{TABLES_BASE}/{schema}/{table}")

def write_delta(df, schema, table):
    (df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true")
        .save(f"{TABLES_BASE}/{schema}/{table}"))
    return df.count()

# CELL ********************

# ---- Customers: dedupe + derive age & tenure ----------------------------------
customers = (read_delta("bronze", "customers")
    .dropDuplicates(["customer_id"])
    .withColumn("age_years",
                F.floor(F.datediff(F.current_date(), F.col("date_of_birth")) / 365.25).cast("int"))
    .withColumn("tenure_years",
                F.floor(F.datediff(F.current_date(), F.col("customer_since")) / 365.25).cast("int"))
    .filter(F.col("age_years").between(18, 100)))
write_delta(customers, "silver", "customers")

# ---- Agents -------------------------------------------------------------------
agents = read_delta("bronze", "agents").dropDuplicates(["agent_id"])
write_delta(agents, "silver", "agents")

# CELL ********************

# ---- Policies: cast + derive annualized + active flag -------------------------
policies = (read_delta("bronze", "policies")
    .dropDuplicates(["policy_id"])
    .withColumn("annual_premium", F.col("annual_premium").cast("double"))
    .withColumn("is_active", (F.col("status") == F.lit("Active")).cast("boolean"))
    .filter(F.col("annual_premium") > 0))
write_delta(policies, "silver", "policies")

# ---- Premium transactions -----------------------------------------------------
txns = (read_delta("bronze", "premium_transactions")
    .dropDuplicates(["txn_id"])
    .withColumn("amount", F.col("amount").cast("double")))
write_delta(txns, "silver", "premium_transactions")

# CELL ********************

# ---- Claims: cast + net incurred + severity bucket ----------------------------
claims = (read_delta("bronze", "claims")
    .dropDuplicates(["claim_id"])
    .withColumn("reported_amount", F.col("reported_amount").cast("double"))
    .withColumn("paid_amount", F.col("paid_amount").cast("double"))
    .withColumn("net_incurred",
                F.when(F.col("claim_status") == "Denied", F.lit(0.0))
                 .otherwise(F.col("paid_amount")))
    .withColumn("severity_band",
                F.when(F.col("reported_amount") < 2500, "Low")
                 .when(F.col("reported_amount") < 25000, "Medium")
                 .otherwise("High")))
write_delta(claims, "silver", "claims")

# ---- Telematics: risk score per event -----------------------------------------
telematics = (read_delta("bronze", "vehicle_telematics")
    .withColumn("risk_points",
                (F.col("harsh_brake").cast("int") * 5)
                + (F.col("harsh_accel").cast("int") * 4)
                + F.when(F.col("speed_mph") > 75, 3).otherwise(0)))
write_delta(telematics, "silver", "vehicle_telematics")

print("silver layer complete")

# CELL ********************

notebookutils.notebook.exit("silver-ok")
