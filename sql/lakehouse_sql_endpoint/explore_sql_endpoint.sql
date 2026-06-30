/* ============================================================================
   explore_sql_endpoint.sql
   Demo queries for the lh_insurance *SQL analytics endpoint* (read-only T-SQL
   over the lakehouse Delta tables). Run these in the SQL analytics endpoint of
   lh_insurance — they prove the endpoint works across dev / test / prod.
   ============================================================================ */

-- 1) Schemas & tables exposed by the endpoint
SELECT table_schema, table_name
FROM INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('bronze','silver','gold')
ORDER BY table_schema, table_name;

-- 2) Portfolio mix by line of business (gold)
SELECT policy_type,
       COUNT(*)                         AS policies,
       CAST(AVG(annual_premium) AS DECIMAL(10,2)) AS avg_premium,
       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_policies
FROM gold.dim_policy
GROUP BY policy_type
ORDER BY policies DESC;

-- 3) Loss ratio trend (gold aggregate)
SELECT year_month, policy_type, earned_premium, incurred_losses, loss_ratio
FROM gold.kpi_monthly
ORDER BY year_month, policy_type;

-- 4) Top 10 customers by incurred losses (joins fact + dim)
SELECT TOP 10
       c.customer_id, c.first_name, c.last_name, c.state,
       SUM(f.net_incurred) AS incurred_losses,
       COUNT(*)            AS claims
FROM gold.fact_claim f
JOIN gold.dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.state
ORDER BY incurred_losses DESC;

-- 5) Suspected fraud rate by severity band
SELECT severity_band,
       COUNT(*)                                  AS claims,
       SUM(CAST(fraud_flag AS INT))              AS suspected_fraud,
       CAST(100.0 * SUM(CAST(fraud_flag AS INT)) / COUNT(*) AS DECIMAL(5,2)) AS fraud_pct
FROM gold.fact_claim
GROUP BY severity_band
ORDER BY fraud_pct DESC;
