-- SQLite. One row per completed purchase order, no split receipts.
SELECT supplier,COUNT(*) AS orders,SUM(otif_flag) AS otif_orders,
 ROUND(100.0*SUM(otif_flag)/COUNT(*),2) AS otif_pct,
 ROUND(100.0*SUM(received_units)/SUM(ordered_units),2) AS unit_fill_pct,
 ROUND(AVG(MAX(0,julianday(receipt_date)-julianday(due_date))),2) AS avg_days_late
FROM purchase_orders GROUP BY supplier ORDER BY supplier;
