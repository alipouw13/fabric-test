CREATE TABLE [dbo].[kpi_monthly] (
	[year_month] varchar(7) NOT NULL,
	[policy_type] varchar(20) NOT NULL,
	[earned_premium] float NULL,
	[incurred_losses] float NULL,
	[claim_count] bigint NULL,
	[fraud_claims] bigint NULL,
	[loss_ratio] float NULL
);
