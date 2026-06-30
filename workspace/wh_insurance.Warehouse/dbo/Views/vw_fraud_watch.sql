CREATE VIEW [dbo].[vw_fraud_watch] AS
SELECT policy_type, severity_band,
       COUNT(*)                                       AS claim_count,
       SUM(CAST(fraud_flag AS INT))                   AS suspected_fraud,
       SUM(reported_amount)                           AS reported_amount,
       SUM(paid_amount)                               AS paid_amount
FROM dbo.fact_claim
GROUP BY policy_type, severity_band;
