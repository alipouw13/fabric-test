/* ============================================================================
   01_build_star_schema_ctas.sql
   Builds the Contoso Insurance Gold star schema in the wh_insurance Warehouse
   directly from the lh_insurance lakehouse GOLD schema using cross-database
   3-part naming (same workspace) + CTAS.

   Run this in the wh_insurance SQL query editor (or via a pipeline Script
   activity). This is the pure-T-SQL alternative to nb_03_load_warehouse, which
   does the same load with the Spark connector.
   ============================================================================ */

-- Dimensions ----------------------------------------------------------------
DROP TABLE IF EXISTS dbo.dim_customer;
CREATE TABLE dbo.dim_customer AS
SELECT * FROM [lh_insurance].[gold].[dim_customer];

DROP TABLE IF EXISTS dbo.dim_agent;
CREATE TABLE dbo.dim_agent AS
SELECT * FROM [lh_insurance].[gold].[dim_agent];

DROP TABLE IF EXISTS dbo.dim_policy;
CREATE TABLE dbo.dim_policy AS
SELECT * FROM [lh_insurance].[gold].[dim_policy];

DROP TABLE IF EXISTS dbo.dim_coverage;
CREATE TABLE dbo.dim_coverage AS
SELECT * FROM [lh_insurance].[gold].[dim_coverage];

DROP TABLE IF EXISTS dbo.dim_date;
CREATE TABLE dbo.dim_date AS
SELECT * FROM [lh_insurance].[gold].[dim_date];

-- Facts ---------------------------------------------------------------------
DROP TABLE IF EXISTS dbo.fact_claim;
CREATE TABLE dbo.fact_claim AS
SELECT * FROM [lh_insurance].[gold].[fact_claim];

DROP TABLE IF EXISTS dbo.fact_premium;
CREATE TABLE dbo.fact_premium AS
SELECT * FROM [lh_insurance].[gold].[fact_premium];

DROP TABLE IF EXISTS dbo.kpi_monthly;
CREATE TABLE dbo.kpi_monthly AS
SELECT * FROM [lh_insurance].[gold].[kpi_monthly];

-- Non-enforced relationships (improve Direct Lake / modeling & query plans) --
ALTER TABLE dbo.fact_claim   ADD CONSTRAINT FK_claim_policy   FOREIGN KEY (policy_id)   REFERENCES dbo.dim_policy(policy_id)   NOT ENFORCED;
ALTER TABLE dbo.fact_claim   ADD CONSTRAINT FK_claim_customer FOREIGN KEY (customer_id) REFERENCES dbo.dim_customer(customer_id) NOT ENFORCED;
ALTER TABLE dbo.fact_claim   ADD CONSTRAINT FK_claim_date     FOREIGN KEY (date_key)    REFERENCES dbo.dim_date(date_key)      NOT ENFORCED;
ALTER TABLE dbo.fact_premium ADD CONSTRAINT FK_prem_policy    FOREIGN KEY (policy_id)   REFERENCES dbo.dim_policy(policy_id)   NOT ENFORCED;
ALTER TABLE dbo.fact_premium ADD CONSTRAINT FK_prem_date      FOREIGN KEY (date_key)    REFERENCES dbo.dim_date(date_key)      NOT ENFORCED;
GO
