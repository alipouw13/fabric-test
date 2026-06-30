CREATE TABLE [dbo].[fact_premium] (
	[txn_id] varchar(13) NOT NULL,
	[policy_id] varchar(12) NULL,
	[customer_id] varchar(10) NULL,
	[agent_id] varchar(10) NULL,
	[policy_type] varchar(20) NULL,
	[date_key] int NULL,
	[txn_date] date NULL,
	[earned_premium] float NULL,
	[payment_method] varchar(20) NULL
);
