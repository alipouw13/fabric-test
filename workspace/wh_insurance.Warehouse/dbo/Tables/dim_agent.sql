CREATE TABLE [dbo].[dim_agent] (
	[agent_id] varchar(10) NOT NULL,
	[agent_name] varchar(100) NULL,
	[region] varchar(10) NULL,
	[channel] varchar(20) NULL,
	[hire_date] date NULL
);
