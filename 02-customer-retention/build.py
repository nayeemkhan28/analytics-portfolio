from pathlib import Path
import csv,json,sqlite3,random
p=Path(__file__).parent
r=random.Random(2811)
rows=[]
for cohort in range(1,7):
 for n in range(100):
  cid=f'C{cohort:02d}{n:03d}'; channel=r.choice(['Organic','Paid','Referral'])
  for age in range(12-cohort+1):
   rows.append((cid,f'2025-{cohort:02d}-01',channel,f'2025-{cohort+age:02d}-01',age))
   if r.random()<{'Organic':.08,'Paid':.14,'Referral':.06}[channel]: break
cols=['customer_id','cohort_month','channel','active_month','month_age']
with (p/'activity.csv').open('w') as f:
 w=csv.writer(f);w.writerow(cols);w.writerows(rows)
con=sqlite3.connect(':memory:');con.execute('CREATE TABLE activity(customer_id TEXT,cohort_month TEXT,channel TEXT,active_month TEXT,month_age INTEGER)');con.executemany('INSERT INTO activity VALUES(?,?,?,?,?)',rows)
sql='''-- Monthly active subscription snapshots. M0 = acquisition month.
SELECT cohort_month, month_age, COUNT(DISTINCT customer_id) AS active_customers,
 ROUND(100.0*COUNT(DISTINCT customer_id)/(SELECT COUNT(DISTINCT b.customer_id) FROM activity b WHERE b.cohort_month=a.cohort_month AND b.month_age=0),2) AS retention_pct
FROM activity a GROUP BY cohort_month,month_age ORDER BY cohort_month,month_age;
SELECT channel, COUNT(DISTINCT CASE WHEN month_age=0 THEN customer_id END) AS acquired,
 COUNT(DISTINCT CASE WHEN month_age=3 THEN customer_id END) AS retained_m3,
 ROUND(100.0*COUNT(DISTINCT CASE WHEN month_age=3 THEN customer_id END)/COUNT(DISTINCT CASE WHEN month_age=0 THEN customer_id END),2) AS retention_m3_pct
FROM activity GROUP BY channel ORDER BY channel;
'''
(p/'analysis.sql').write_text(sql)
queries=sql.split(';'); cohort=con.execute(queries[0]).fetchall(); channels=con.execute(queries[1]).fetchall()
assert len({(x[0],x[3]) for x in rows})==len(rows)
assert len({x[0] for x in rows})==600
assert all(sum(x[0]==cid and x[4]==0 for x in rows)==1 for cid in {x[0] for x in rows})
assert all(0<=v[3]<=100 for v in cohort)
assert all(sum(x[1]==c and x[4]==3 for x in rows)==count for c,a,count,pct in cohort if a==3)
assert sum(x[1] for x in channels)==600
m3=sum(x[2] for x in channels); pct=m3/600*100
result={'acquired':600,'retained_m3':m3,'retention_m3_pct':pct,'cohort_rows':cohort,'channel_m3':channels,'validation':'passed: unique customer-months, acquisition keys, bounds, independent M3 counts, segment reconciliation'}
(p/'results.json').write_text(json.dumps(result,indent=2))
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620"><rect width="1000" height="620" fill="#111d2c"/><g font-family="Arial" fill="#f2f7ff"><text x="40" y="50" font-size="28">Customer retention | acquisition cohorts</text><text x="40" y="85">Synthetic subscription scenario • January–June 2025 cohorts • observed through December</text>'
svg+=f'<text x="40" y="145" font-size="30">600 acquired     {m3} active at M3     {pct:.1f}% M3 retention</text><text x="40" y="210" font-size="22">M3 retention by acquisition channel</text>'
for i,(channel,total,retained,rate) in enumerate(channels):
 y=265+i*80
 svg+=f'<text x="40" y="{y}">{channel} (n={total})</text><rect x="240" y="{y-22}" width="{rate*6}" height="32" fill="#4ed9ba"/><text x="{255+rate*6}" y="{y}">{rate:.1f}%</text>'
svg+='<text x="40" y="535">M3 = active three calendar months after acquisition; denominator = acquired cohort.</text><text x="40" y="575">Illustrative data: channel differences are built into the generator, not causal evidence.</text></g></svg>'
(p/'dashboard.svg').write_text(svg)
(p/'README.md').write_text(f'''# Customer retention and cohort analysis

A reproducible subscription analytics case study using **original synthetic data**. No real customers, company metrics or external dataset.

## Business question and decision
A fictional subscription team wants to know how retention differs by acquisition channel and when cohorts lose subscribers. Use the analysis to prioritize an onboarding experiment and determine whether acquisition volume is translating into sustained activity.

## Findings
- 600 customers acquired across January–June 2025; {m3} still active at month 3: **{pct:.2f}% M3 retention**.
- Channel M3 retention: {', '.join(f'{c}: {v:.2f}% ({k}/{n})' for c,n,k,v in channels)}.
- These differences are deliberately generated using channel-specific dropout probabilities. They are illustrative associations, not estimates of real channel quality or causal effects.

![Retention dashboard](dashboard.svg)

## Recommendations
Investigate Paid onboarding first, then run a randomized onboarding experiment within channel. Measure M3 retention alongside acquisition cost and contribution margin before reallocating budget. This dataset contains neither acquisition costs nor revenue, so ROI and lifetime value cannot be inferred. Experiment success criteria should be agreed before launch; historical channel differences alone do not justify a budget change.

## Method and KPI contract
One row per active customer per calendar month. M0 is acquisition month. M3 retention = distinct customers active at cohort month + 3 divided by distinct acquired customers. All six cohorts have at least three months of follow-up by the 2025-12 observation cutoff. Later-month comparisons must use equally mature cohorts; do not treat unobserved ages as zero retention. Generator models permanent dropout with no reactivation. It is not a churn prediction model. Absence after the last observed month cannot prove a future cancellation.

## Reproduce and validate
Run `python3 build.py` with Python 3 (standard library only). Outputs: activity.csv, analysis.sql, results.json, dashboard.svg and README.md. Seed 2811; 100 customers per cohort; channel-specific monthly dropout probabilities Organic 8%, Paid 14%, Referral 6%. Dropout occurs after that month's activity. Assertions validate unique customer-months, 600 acquisition keys, retention bounds, independent M3 counts and channel denominator reconciliation. SQL runs against an in-memory SQLite database. results.json contains the full cohort table and segment calculations.

Full activity.csv is generated locally by the build command; activity-sample.csv contains the first 30 rows for preview only. Do not calculate portfolio KPIs from the preview.

## Data dictionary
|Field|Meaning|
|---|---|
|customer_id|Synthetic customer key, no personal information|
|cohort_month|First active month, ISO date, first of month|
|channel|Organic, Paid or Referral; fixed per customer|
|active_month|Month in which subscription is active, ISO date|
|month_age|Integer calendar month offset from acquisition, M0 onward|

## Power BI build guide
No PBIX file is included or claimed. Import activity.csv; use Date for both month columns and Whole number for month_age. For this cohort report use cohort_month, channel and month_age slicers; do not apply active_month filters to the acquisition denominator. Create:

```dax
Active Customers = DISTINCTCOUNT(activity[customer_id])
Acquired Customers = CALCULATE(DISTINCTCOUNT(activity[customer_id]), REMOVEFILTERS(activity[month_age]), activity[month_age] = 0)
Cohort Retention = DIVIDE([Active Customers], [Acquired Customers])
```

Format retention as a percentage. Matrix: cohort_month rows, month_age columns, Cohort Retention values with heatmap formatting. Chart: channel vs Cohort Retention filtered to month_age=3. Acceptance checks: M0 is 100% for every cohort; M3 total is {pct:.2f}%; channel counts match results.json. Show cohort sizes and observation cutoff prominently. A date table and explicit maturity measures are needed before extending this guide to rolling live cohorts. dashboard.svg is a static analysis visual, not a Power BI export.
''')
print(json.dumps({'customers':600,'m3':m3,'pct':pct,'checks':'passed'}))
