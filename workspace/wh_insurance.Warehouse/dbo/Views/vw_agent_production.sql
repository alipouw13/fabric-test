CREATE VIEW [dbo].[vw_agent_production] AS
SELECT
    a.agent_id, a.agent_name, a.region, a.channel,
    COUNT(DISTINCT pol.policy_id)        AS policies_sold,
    SUM(pol.annual_premium)              AS total_annual_premium,
    SUM(ISNULL(fc.net_incurred,0))       AS incurred_losses
FROM dbo.dim_agent a
LEFT JOIN dbo.dim_policy pol ON pol.agent_id = a.agent_id
LEFT JOIN dbo.fact_claim fc  ON fc.policy_id = pol.policy_id
GROUP BY a.agent_id, a.agent_name, a.region, a.channel;
