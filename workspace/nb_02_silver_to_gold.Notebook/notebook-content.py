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

# # nb_02 — Silver ➜ Gold (star schema)
#
# Builds the **gold** dimensional model consumed by the Warehouse and the
# Power BI semantic model:
#
# * Dimensions: `dim_customer`, `dim_agent`, `dim_policy`, `dim_coverage`, `dim_date`
# * Facts: `fact_claim` (claim grain), `fact_premium` (installment grain)
# * Aggregate: `kpi_monthly` (loss ratio by month & policy type)

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

customers = read_delta("silver", "customers")
agents = read_delta("silver", "agents")
policies = read_delta("silver", "policies")
claims = read_delta("silver", "claims")
txns = read_delta("silver", "premium_transactions")

# CELL ********************

# ---- Dimensions ---------------------------------------------------------------
dim_customer = customers.select(
    "customer_id", "first_name", "last_name", "email", "gender",
    "city", "state", "postal_code", "credit_tier", "age_years", "tenure_years")
write_delta(dim_customer, "gold", "dim_customer")

dim_agent = agents.select("agent_id", "agent_name", "region", "channel", "hire_date")
write_delta(dim_agent, "gold", "dim_agent")

dim_policy = policies.select(
    "policy_id", "customer_id", "agent_id", "policy_type", "product",
    "term_months", "status", "is_active", "annual_premium", "deductible", "coverage_limit")
write_delta(dim_policy, "gold", "dim_policy")

# Small conformed coverage dimension
dim_coverage = spark.createDataFrame(
    [("Auto", "Personal Lines", "Short-tail"),
     ("Home", "Personal Lines", "Long-tail"),
     ("Life", "Life & Health", "Long-tail"),
     ("Umbrella", "Specialty", "Long-tail")],
    ["policy_type", "line_of_business", "tail_type"])
write_delta(dim_coverage, "gold", "dim_coverage")

# CELL ********************

# ---- Date dimension (spanning all transactional dates) ------------------------
bounds = (claims.select(F.min("claim_date").alias("mn"), F.max("claim_date").alias("mx"))
          .union(txns.select(F.min("txn_date"), F.max("txn_date")))
          .agg(F.min("mn").alias("mn"), F.max("mx").alias("mx")).collect()[0])

dim_date = (spark.sql(
        f"SELECT explode(sequence(to_date('{bounds['mn']}'), to_date('{bounds['mx']}'), interval 1 day)) AS date")
    .withColumn("date_key", F.date_format("date", "yyyyMMdd").cast("int"))
    .withColumn("year", F.year("date"))
    .withColumn("quarter", F.quarter("date"))
    .withColumn("month", F.month("date"))
    .withColumn("month_name", F.date_format("date", "MMMM"))
    .withColumn("day_of_month", F.dayofmonth("date"))
    .withColumn("year_month", F.date_format("date", "yyyy-MM")))
write_delta(dim_date, "gold", "dim_date")

# CELL ********************

# ---- Facts --------------------------------------------------------------------
fact_claim = (claims.alias("c")
    .join(policies.alias("p"), "policy_id", "left")
    .select(
        F.col("c.claim_id"),
        F.col("c.policy_id"),
        F.col("c.customer_id"),
        F.col("p.agent_id"),
        F.col("p.policy_type"),
        F.date_format("c.claim_date", "yyyyMMdd").cast("int").alias("date_key"),
        F.col("c.claim_date"),
        F.col("c.loss_type"),
        F.col("c.claim_status"),
        F.col("c.severity_band"),
        F.col("c.reported_amount"),
        F.col("c.paid_amount"),
        F.col("c.net_incurred"),
        F.col("c.fraud_flag"),
        F.col("c.catastrophe_flag")))
write_delta(fact_claim, "gold", "fact_claim")

fact_premium = (txns.alias("t")
    .join(policies.alias("p"), "policy_id", "left")
    .select(
        F.col("t.txn_id"),
        F.col("t.policy_id"),
        F.col("p.customer_id"),
        F.col("p.agent_id"),
        F.col("p.policy_type"),
        F.date_format("t.txn_date", "yyyyMMdd").cast("int").alias("date_key"),
        F.col("t.txn_date"),
        F.col("t.amount").alias("earned_premium"),
        F.col("t.payment_method")))
write_delta(fact_premium, "gold", "fact_premium")

# CELL ********************

# ---- Monthly KPI aggregate (loss ratio) ---------------------------------------
prem_m = (fact_premium.groupBy(F.date_format("txn_date", "yyyy-MM").alias("year_month"), "policy_type")
          .agg(F.sum("earned_premium").alias("earned_premium")))
loss_m = (fact_claim.groupBy(F.date_format("claim_date", "yyyy-MM").alias("year_month"), "policy_type")
          .agg(F.sum("net_incurred").alias("incurred_losses"),
               F.count("*").alias("claim_count"),
               F.sum(F.col("fraud_flag").cast("int")).alias("fraud_claims")))

kpi_monthly = (prem_m.join(loss_m, ["year_month", "policy_type"], "outer")
    .fillna(0, ["earned_premium", "incurred_losses", "claim_count", "fraud_claims"])
    .withColumn("loss_ratio",
                F.when(F.col("earned_premium") > 0,
                       F.round(F.col("incurred_losses") / F.col("earned_premium"), 4))
                 .otherwise(F.lit(None))))
write_delta(kpi_monthly, "gold", "kpi_monthly")

print("gold star schema complete")

# CELL ********************

notebookutils.notebook.exit("gold-ok")
