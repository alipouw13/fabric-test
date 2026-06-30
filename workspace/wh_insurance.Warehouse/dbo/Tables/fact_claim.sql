CREATE TABLE [dbo].[fact_claim] (
	[claim_id] varchar(12) NOT NULL,
	[policy_id] varchar(12) NULL,
	[customer_id] varchar(10) NULL,
	[agent_id] varchar(10) NULL,
	[policy_type] varchar(20) NULL,
	[date_key] int NULL,
	[claim_date] date NULL,
	[loss_type] varchar(30) NULL,
	[claim_status] varchar(20) NULL,
	[severity_band] varchar(10) NULL,
	[reported_amount] float NULL,
	[paid_amount] float NULL,
	[net_incurred] float NULL,
	[fraud_flag] bit NULL,
	[catastrophe_flag] bit NULL
);
