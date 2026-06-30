CREATE TABLE [dbo].[dim_policy] (
	[policy_id] varchar(12) NOT NULL,
	[customer_id] varchar(10) NULL,
	[agent_id] varchar(10) NULL,
	[policy_type] varchar(20) NULL,
	[product] varchar(50) NULL,
	[term_months] int NULL,
	[status] varchar(20) NULL,
	[is_active] bit NULL,
	[annual_premium] float NULL,
	[deductible] int NULL,
	[coverage_limit] int NULL
);
