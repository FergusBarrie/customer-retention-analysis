# Customer Behaviour and Retention Analysis

A cohort and retention analysis of 23,570 customers of an online CD retailer, tracked from
their first purchase for up to 18 months.

**Business question:** Of the customers this retailer acquired, how many came back, how
quickly did activity fall away, and how much is an acquired customer actually worth?

| | |
|---|---|
| **Tools** | SQLite (SQL), Python (pandas, matplotlib) |
| **Dataset** | [CDNOW master dataset](https://www.brucehardie.com/datasets/), published by Bruce Hardie |
| **Period** | 1 January 1997 to 30 June 1998 |
| **Size** | 69,659 transaction lines, 67,591 orders, 23,570 customers |

### Why this dataset

It is an unusual and useful shape. Every customer in the file made their **first ever**
purchase at CDNOW during the first quarter of 1997, and the file then records everything
they bought for up to 18 months. That means retention is **measured, not estimated** —
there is no ambiguity about when a customer joined and no left-censoring.

It is old data (1997–98), and I say so plainly. I chose it because it is the right shape
for learning cohort analysis properly, not because it describes today's market.

---

## Headline numbers

| Metric | Value |
|---|---|
| Customers | 23,570 |
| Orders | 67,591 |
| Revenue | $2,500,316 |
| Average order value | $36.99 |
| Revenue per customer (18 months) | $106.08 |
| Average orders per customer | 2.87 |
| Customers who ordered more than once | 48.9% |

## What I found

1. **Half of all customers never came back, and they are only a seventh of revenue.**
   51.1% of customers placed exactly one order. Together they produced 14.7% of revenue.
   The other 48.9% produced the rest.

2. **Retention drops off a cliff in month one and then holds steady.** Of each cohort,
   about 14.9% placed an order in the month after their first purchase. From month six
   onwards it settles at roughly **7.4%** active in any given month, and stays there — it
   does not keep decaying. The business is a small, steady base of regulars plus a large
   group who bought once and vanished.

3. **The three acquisition cohorts behave almost identically.** Repeat rates of 48.1% to
   49.3%, and revenue per customer within $7 of each other over the first 15 months. That
   consistency matters: it means the retention curve is a stable property of this business
   rather than an artifact of one month's intake.

4. **The first order is only about a third of what a customer is worth.** Over the first
   15 months, an acquired customer generated **$102.74** on average — of which $38.08
   (37.1%) came from the first order. The remaining 63% depended entirely on them coming
   back.

5. **Each repeat order makes the next one more likely, and larger.** 51.1% of customers
   never ordered a second time; after a third order only 29.5% stop, and by the tenth
   order about 17%. Average order value rises alongside, from $33.29 on a first order to
   $43.30 on a tenth.

6. **Revenue is very concentrated.** The highest-spending 10% of customers produced
   **50.9%** of revenue, averaging $540 each. The top 20% produced 67.7%.

7. **If a customer comes back at all, they usually come back quickly.** 35.7% of repeat
   buyers placed their second order within a month, and 59.8% within three months.

## What I would suggest doing about it

1. **Concentrate on the second order, in the first month.** It is the single biggest
   break point: 51.1% of customers are lost there, against 29.5% after a third order. And
   the timing is clear — most people who do come back do so within a month, so a follow-up
   at six weeks is largely talking to people who have already gone.

2. **Judge acquisition on the 15-month figure, not the first order.** A channel that looks
   unprofitable against a $38 first order may be comfortably profitable against $102.74.
   This analysis gives a defensible number to use.

3. **Treat the top decile as a distinct group.** 2,357 customers averaging $540 each
   produce half the revenue. They deserve separate measurement — at minimum, tracking
   whether that group is growing or shrinking, which total revenue would hide.

I have not put a monetary value on any of these. The dataset contains no acquisition
costs, no marketing spend and no margin, so any claim about return on investment would be
invented.

## Limitations

- **The data is from 1997–98.** Online retail was a different business. The *method*
  transfers; the specific percentages should not be quoted as benchmarks.
- **No product, channel or marketing data.** Just customer, date, quantity and value. So
  this analysis can describe *what* customers did but says nothing about *why*, and
  nothing about what it cost to acquire them.
- **Only three acquisition cohorts, all from one quarter.** There is no way to tell
  whether retention differs by season or has a trend.
- **The comparison window is capped at 15 months.** The data ends in June 1998, so the
  January cohort has 17 months of history, February 16 and March 15. All cross-cohort
  comparisons use the first 15 months, which is all three have.
- **"Retention" here means placing an order in a given month.** It is not a subscription,
  so a customer who buys in months 2 and 9 is simply inactive in between, not churned and
  returned. Customers are never marked as lost.
- **Value by order number is affected by survivorship.** Customers who reach a tenth order
  are the keenest buyers by definition, so part of the rise in average order value is
  selection rather than customers genuinely spending more over time.
- **255 rows (0.37%) are exact duplicates.** I kept them, since they may be two identical
  items bought the same day and this is the published version of the dataset. They are
  0.17% of revenue, so no conclusion here depends on the choice.

---

## How to reproduce this

```bash
pip install pandas matplotlib

python scripts/00_download_data.py       # fetch the dataset (small zip)
python scripts/01_clean_data.py          # build orders and customers, load SQLite
python scripts/02_run_sql.py             # run every query in sql/, save CSVs
python scripts/03_make_charts.py         # build the charts
python scripts/04_export_for_website.py  # JSON for the portfolio site
```

The whole pipeline runs in well under a minute.

To explore the database:

```bash
sqlite3 data/clean/cdnow.db
sqlite> .mode column
sqlite> .headers on
sqlite> .read sql/03_cohort_retention.sql
```

## What is in this repository

```
data/raw/        CDNOW_master.txt (not committed - run 00_download_data.py)
data/clean/      transactions.csv, orders.csv, customers.csv, cdnow.db
scripts/         00 download, 01 clean, 02 run SQL, 03 charts, 04 website export
sql/             10 .sql files, each with comments explaining the query
outputs/tables/  one CSV per query, plus the two cohort matrices
outputs/charts/  nine PNG charts
outputs/         cleaning_log.txt and website_data.json
FINDINGS.md      the full write-up
LEARNING_GUIDE.md  how the cohort analysis works, with exercises
```

## The three tables

A row in the raw file is a transaction **line**, not an order. Getting this right is the
first real decision in the project.

| Table | Grain | Rows |
|---|---|---|
| `transactions` | one line per product line | 69,659 |
| `orders` | one row per customer per day | 67,591 |
| `customers` | one row per customer, with cohort and totals | 23,570 |

2.6% of orders have more than one line. Measuring purchase frequency from `transactions`
would overstate how often people bought and understate order value.

## Honest note on this project

I built this to learn how cohort analysis actually works — how the month index is
constructed, why the cohort table has ragged edges, and what retention does and does not
mean when there is no subscription. The [learning guide](LEARNING_GUIDE.md) walks through
all of it, including a bug I had to fix in my own export script. I can talk through any
query in this repository line by line.
