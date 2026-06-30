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

# # nb_03 — Load Warehouse (gold ➜ wh_insurance)
#
# Publishes the curated **gold** star schema into the `wh_insurance` Warehouse using the
# **Fabric Spark connector for Data Warehouse** (`synapsesql`). The warehouse then serves
# the Power BI semantic model and ad-hoc T-SQL.
#
# The warehouse name is read from the **Variable Library** (`vl_insurance_config`) so it can
# differ per environment; it falls back to the literal default if the library is unavailable.

# CELL ********************

import notebookutils
from pyspark.sql import functions as F

LAKEHOUSE_NAME = "lh_insurance"

# Resolve target warehouse name from the Variable Library (dev/test/prod aware)
try:
    cfg = notebookutils.variableLibrary.getLibrary("vl_insurance_config")
    WAREHOUSE_NAME = cfg.warehouse_name
except Exception as e:
    print(f"Variable Library unavailable ({e}); using default.")
    WAREHOUSE_NAME = "wh_insurance"

WORKSPACE_ID = notebookutils.runtime.context["currentWorkspaceId"]
LAKEHOUSE_ID = notebookutils.lakehouse.get(LAKEHOUSE_NAME)["id"]
TABLES_BASE = f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}/Tables"
print(f"Target warehouse: {WAREHOUSE_NAME}")

# CELL ********************

GOLD_TABLES = [
    "dim_customer", "dim_agent", "dim_policy", "dim_coverage",
    "dim_date", "fact_claim", "fact_premium", "kpi_monthly",
]

for t in GOLD_TABLES:
    df = spark.read.format("delta").load(f"{TABLES_BASE}/gold/{t}")
    # The Spark connector creates/overwrites the warehouse table in the dbo schema
    df.write.mode("overwrite").synapsesql(f"{WAREHOUSE_NAME}.dbo.{t}")
    print(f"loaded {WAREHOUSE_NAME}.dbo.{t:<14} rows={df.count()}")

# CELL ********************

notebookutils.notebook.exit(f"warehouse-loaded:{WAREHOUSE_NAME}")
