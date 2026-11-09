-- SQLite; all monetary inputs are integer CAD cents.
SELECT COUNT(*) AS lines, SUM(sales_cents)/100.0 AS revenue,
 SUM(gross_profit_cents)/100.0 AS gross_profit,
 100.0*SUM(gross_profit_cents)/SUM(sales_cents) AS margin_pct FROM sales;
SELECT category, SUM(sales_cents)/100.0 AS revenue, SUM(gross_profit_cents)/100.0 AS gross_profit,
 100.0*SUM(gross_profit_cents)/SUM(sales_cents) AS margin_pct FROM sales GROUP BY category;
SELECT discount_pct, SUM(sales_cents)/100.0 AS revenue,
 100.0*SUM(gross_profit_cents)/SUM(sales_cents) AS margin_pct FROM sales GROUP BY discount_pct;
