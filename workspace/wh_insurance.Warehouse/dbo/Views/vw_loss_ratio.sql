CREATE VIEW [dbo].[vw_loss_ratio] AS
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
