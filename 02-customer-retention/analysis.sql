-- Monthly active subscription snapshots. M0 = acquisition month.
SELECT cohort_month, month_age, COUNT(DISTINCT customer_id) AS active_customers,
 ROUND(100.0*COUNT(DISTINCT customer_id)/(SELECT COUNT(DISTINCT b.customer_id) FROM activity b WHERE b.cohort_month=a.cohort_month AND b.month_age=0),2) AS retention_pct
FROM activity a GROUP BY cohort_month,month_age ORDER BY cohort_month,month_age;
SELECT channel, COUNT(DISTINCT CASE WHEN month_age=0 THEN customer_id END) AS acquired,
 COUNT(DISTINCT CASE WHEN month_age=3 THEN customer_id END) AS retained_m3,
 ROUND(100.0*COUNT(DISTINCT CASE WHEN month_age=3 THEN customer_id END)/COUNT(DISTINCT CASE WHEN month_age=0 THEN customer_id END),2) AS retention_m3_pct
FROM activity GROUP BY channel ORDER BY channel;
