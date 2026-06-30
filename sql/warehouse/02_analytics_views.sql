/* ============================================================================
   02_analytics_views.sql
   Business-friendly views + a loss-ratio stored procedure over the
   wh_insurance star schema. These back the Power BI semantic model and
   ad-hoc analytics.
   ============================================================================ */

-- Earned premium vs incurred losses by month & line of business --------------
CREATE OR ALTER VIEW dbo.vw_loss_ratio AS
SELECT
    p.year_month,
    p.policy_type,
    c.line_of_business,
    p.earned_premium,
    ISNULL(l.incurred_losses, 0)            AS incurred_losses,
    ISNULL(l.claim_count, 0)                AS claim_count,
    CASE WHEN p.earned_premium > 0
         THEN CAST(ISNULL(l.incurred_losses,0) / p.earned_premium AS DECIMAL(10,4))
         ELSE NULL END                      AS loss_ratio
FROM (
    SELECT FORMAT(txn_date,'yyyy-MM') AS year_month, policy_type,
           SUM(earned_premium) AS earned_premium
    FROM dbo.fact_premium GROUP BY FORMAT(txn_date,'yyyy-MM'), policy_type
) p
LEFT JOIN (
    SELECT FORMAT(claim_date,'yyyy-MM') AS year_month, policy_type,
           SUM(net_incurred) AS incurred_losses, COUNT(*) AS claim_count
    FROM dbo.fact_claim GROUP BY FORMAT(claim_date,'yyyy-MM'), policy_type
) l ON p.year_month = l.year_month AND p.policy_type = l.policy_type
LEFT JOIN dbo.dim_coverage c ON p.policy_type = c.policy_type;
GO

-- Agent production leaderboard -----------------------------------------------
CREATE OR ALTER VIEW dbo.vw_agent_production AS
SELECT
    a.agent_id, a.agent_name, a.region, a.channel,
    COUNT(DISTINCT pol.policy_id)        AS policies_sold,
    SUM(pol.annual_premium)              AS total_annual_premium,
    SUM(ISNULL(fc.net_incurred,0))       AS incurred_losses
FROM dbo.dim_agent a
LEFT JOIN dbo.dim_policy pol ON pol.agent_id = a.agent_id
LEFT JOIN dbo.fact_claim fc  ON fc.policy_id = pol.policy_id
GROUP BY a.agent_id, a.agent_name, a.region, a.channel;
GO

-- Fraud watch ----------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_fraud_watch AS
SELECT policy_type, severity_band,
       COUNT(*)                                       AS claim_count,
       SUM(CAST(fraud_flag AS INT))                   AS suspected_fraud,
       SUM(reported_amount)                           AS reported_amount,
       SUM(paid_amount)                               AS paid_amount
FROM dbo.fact_claim
GROUP BY policy_type, severity_band;
GO

-- Parameterized loss-ratio proc ---------------------------------------------
CREATE OR ALTER PROCEDURE dbo.usp_loss_ratio_by_year @year INT AS
BEGIN
    SELECT policy_type,
           SUM(earned_premium)  AS earned_premium,
           SUM(incurred_losses) AS incurred_losses,
           CASE WHEN SUM(earned_premium) > 0
                THEN CAST(SUM(incurred_losses)/SUM(earned_premium) AS DECIMAL(10,4))
                ELSE NULL END   AS loss_ratio
    FROM dbo.vw_loss_ratio
    WHERE LEFT(year_month,4) = CAST(@year AS VARCHAR(4))
    GROUP BY policy_type
    ORDER BY loss_ratio DESC;
END
GO
