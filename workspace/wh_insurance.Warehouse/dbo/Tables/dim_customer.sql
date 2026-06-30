CREATE TABLE [dbo].[dim_customer] (
	[customer_id] varchar(10) NOT NULL,
	[first_name] varchar(50) NULL,
	[last_name] varchar(50) NULL,
	[email] varchar(200) NULL,
	[gender] varchar(10) NULL,
	[city] varchar(50) NULL,
	[state] varchar(2) NULL,
	[postal_code] varchar(10) NULL,
	[credit_tier] varchar(20) NULL,
	[age_years] int NULL,
	[tenure_years] int NULL
);
