from pathlib import Path
import csv,sqlite3,json,random,datetime
p=Path(__file__).parent;r=random.Random(2823);rows=[]
for i in range(180):
 supplier=['Atlas','Birch','Cedar'][i%3];ordered=r.randint(20,100);received=ordered-r.choice([0,0,0,5,10]);due=datetime.date(2025,9,1)+datetime.timedelta(days=i//3);late=r.choice({'Atlas':[-2,0,0,1],'Birch':[0,1,3,5],'Cedar':[-1,0,0,2]}[supplier]);actual=due+datetime.timedelta(days=late)
 rows.append((i+1,supplier,ordered,received,due.isoformat(),actual.isoformat(),int(actual<=due and received==ordered)))
cols=['po_id','supplier','ordered_units','received_units','due_date','receipt_date','otif_flag']
with (p/'purchase_orders.csv').open('w') as f:
 w=csv.writer(f);w.writerow(cols);w.writerows(rows)
sql='''-- SQLite. One row per completed purchase order, no split receipts.
SELECT supplier,COUNT(*) AS orders,SUM(otif_flag) AS otif_orders,
 ROUND(100.0*SUM(otif_flag)/COUNT(*),2) AS otif_pct,
 ROUND(100.0*SUM(received_units)/SUM(ordered_units),2) AS unit_fill_pct,
 ROUND(AVG(MAX(0,julianday(receipt_date)-julianday(due_date))),2) AS avg_days_late
FROM purchase_orders GROUP BY supplier ORDER BY supplier;
'''
(p/'analysis.sql').write_text(sql)
c=sqlite3.connect(':memory:');c.execute('CREATE TABLE purchase_orders(po_id INTEGER,supplier TEXT,ordered_units INTEGER,received_units INTEGER,due_date TEXT,receipt_date TEXT,otif_flag INTEGER)');c.executemany('INSERT INTO purchase_orders VALUES(?,?,?,?,?,?,?)',rows);result=c.execute(sql).fetchall()
assert len({x[0] for x in rows})==180
assert all(0<=x[3]<=x[2] and x[6]==int(x[5]<=x[4] and x[2]==x[3]) for x in rows)
assert sum(x[1] for x in result)==180
assert sum(x[2] for x in result)==sum(x[6] for x in rows)
for s,n,k,rate,fill,days in result:
 subset=[x for x in rows if x[1]==s];assert round(sum(x[3] for x in subset)/sum(x[2] for x in subset)*100,2)==fill
k=sum(x[6] for x in rows);rate=k/180*100
(p/'results.json').write_text(json.dumps({'orders':180,'otif_orders':k,'otif_pct':rate,'columns':['supplier','orders','otif_orders','otif_pct','unit_fill_pct','avg_days_late'],'suppliers':result,'validation':'passed: unique PO keys, quantity bounds, OTIF definition, supplier reconciliation, independent weighted fill rates'},indent=2))
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="580" viewBox="0 0 1000 580"><rect width="1000" height="580" fill="#122031"/><g font-family="Arial" fill="#f3f7ff"><text x="40" y="50" font-size="28">Supplier delivery performance</text><text x="40" y="85">Synthetic completed purchase orders | Due September–October 2025</text>'
svg+=f'<text x="40" y="145" font-size="30">180 orders     {k} OTIF orders     {rate:.1f}% OTIF</text><text x="40" y="210" font-size="22">On time and in full by supplier</text>'
for i,(s,n,k,rt,fill,days) in enumerate(result):
 y=265+i*75;svg+=f'<text x="40" y="{y}">{s} (n={n})</text><rect x="210" y="{y-22}" width="{rt*7}" height="30" fill="#54d8b8"/><text x="{225+rt*7}" y="{y}">{rt:.1f}%</text>'
svg+='<text x="40" y="520">OTIF requires receipt by due date AND all ordered units received.</text><text x="40" y="550">Illustrative scenario; completed-order selection excludes open-order risk.</text></g></svg>'; (p/'dashboard.svg').write_text(svg)
(p/'README.md').write_text(f'''# Supplier delivery performance and supply chain analysis

Original synthetic case study · Python · SQLite · KPI design · Power BI guide

## Business brief
A fictional procurement manager needs to identify suppliers requiring a delivery improvement plan. The analysis separates order-level on-time-in-full (OTIF) from unit-weighted fill rate. The decision is where to investigate delivery reliability before changing sourcing allocations.

## Findings
Across 180 completed purchase orders, **{sum(x[6] for x in rows)} met OTIF ({rate:.2f}%)**.

|Supplier|Orders|OTIF %|Unit fill %|Average days late|
|---|---:|---:|---:|---:|
'''+''.join(f'|{s}|{n}|{rt:.2f}|{fill:.2f}|{days:.2f}|\n' for s,n,k,rt,fill,days in result)+'''
![Delivery dashboard](dashboard.svg)

## Recommendations and limitations
Start a delivery root-cause review with Birch, whose modeled delays are more frequent. Review due-date accuracy, transport milestones and shortage reasons before negotiating a corrective-action plan. Monitor OTIF and fill rate together: high unit fill can coexist with poor delivery timing. Supplier delay distributions are deliberately built into this generator; this is not real supplier evidence or proof that any sourcing change will improve service. Cost, quality, lead time, demand, inventory and open orders are absent, so this project does not estimate inventory savings or recommend order quantities.

## KPI contract
- OTIF: completed POs received on or before due date AND received_units = ordered_units, divided by all completed POs. Each order has equal weight.
- Unit fill: SUM(received_units)/SUM(ordered_units); quantity weighted, not average order fill.
- Average days late: mean MAX(0, receipt_date − due_date), including on-time orders as zero. Calendar days, not business days.
- Scope: one final receipt per PO; no split shipments, cancellations, returns or open POs. Due dates span 2025-09-01 to 2025-10-30. Include open overdue POs in a production scorecard to avoid completed-order selection bias.

## Reproduce
Run `python3 build.py` (Python 3 standard library only). It regenerates the full 180-row purchase_orders.csv, analysis.sql, results.json, dashboard.svg and this README. SQL executes in an in-memory SQLite database. Seed 2823; 60 POs per supplier. Ordered units 20–100; shortages sampled from [0,0,0,5,10]. Delays sampled by supplier as defined in build.py. The CSV is original synthetic data with no external licensing dependency or personal information.

## Validation
Assertions check unique PO keys, quantity bounds, row-level OTIF logic, supplier order and OTIF reconciliations, and independently calculated weighted fill rates. All passed on generation. Saved results include query column names. Acceptance examples: an early short delivery fails OTIF; a late complete delivery also fails; an exact-due-date complete delivery passes.

## Data dictionary
|Field|Definition|
|---|---|
|po_id|Unique synthetic purchase order integer|
|supplier|Fictional Atlas, Birch or Cedar|
|ordered_units|Positive integer quantity requested|
|received_units|Final received units; never above ordered quantity|
|due_date|Agreed due date, ISO YYYY-MM-DD|
|receipt_date|Final receipt date, ISO YYYY-MM-DD|
|otif_flag|1 if on time and complete, else 0|

## Power BI implementation
No PBIX is included or claimed. Import purchase_orders.csv. Set due_date and receipt_date to Date; quantities, po_id and otif_flag to Whole number. Use supplier and due-month slicers. Create:

```dax
Orders = COUNTROWS(purchase_orders)
OTIF Orders = SUM(purchase_orders[otif_flag])
OTIF Rate = DIVIDE([OTIF Orders], [Orders])
Unit Fill Rate = DIVIDE(SUM(purchase_orders[received_units]), SUM(purchase_orders[ordered_units]))
```

Format rates as percentages. Cards: Orders, OTIF Orders, OTIF Rate, Unit Fill Rate. Bar chart: supplier versus OTIF Rate; table: supplier, order count, OTIF, fill. A date dimension should relate to due_date for due-period reporting; receipt-date reporting needs a separate relationship definition. Unsliced and supplier-filtered metrics must match results.json. dashboard.svg is a static analysis visual, not a Power BI report export.
''')
(p/'linkedin-draft.md').write_text(f'''New portfolio case study: supplier delivery performance.\n\nI built a reproducible Python/SQLite analysis of 180 synthetic purchase orders. Overall OTIF was {rate:.2f}%. The project distinguishes order-level delivery reliability from unit-weighted fill rate and documents why completed-order reports can miss open-order risk.\n\nIncludes full synthetic data, SQL, validation checks, a dashboard visual, business recommendations and a Power BI implementation guide. Figures are illustrative, not real supplier performance. No PBIX is included.\n\nhttps://github.com/nayeemkhan28/analytics-portfolio/tree/main/03-supply-chain\n\n#DataAnalytics #SQL #SupplyChain #PowerBI\n''')
print(json.dumps({'otif_pct':rate,'suppliers':result,'checks':'passed'}))
