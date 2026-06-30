CREATE PROCEDURE [dbo].[usp_loss_ratio_by_year] @year INT AS
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
