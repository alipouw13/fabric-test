CREATE TABLE [dbo].[dim_date] (
	[date] date NOT NULL,
	[date_key] int NOT NULL,
	[year] int NULL,
	[quarter] int NULL,
	[month] int NULL,
	[month_name] varchar(20) NULL,
	[day_of_month] int NULL,
	[year_month] varchar(7) NULL
);
