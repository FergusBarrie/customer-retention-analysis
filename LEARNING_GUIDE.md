# Learning guide — Customer Behaviour and Retention Analysis

This guide explains how the cohort analysis actually works, so I can talk through it rather
than just display the output. Cohort analysis is one of those topics where the chart looks
simple and the construction is where all the mistakes live.

Open the database alongside this:

```bash
sqlite3 data/clean/cdnow.db
sqlite> .mode column
sqlite> .headers on
```

---

## 1. The dataset, and why its shape matters

CDNOW was an online CD retailer. This file is the complete purchase history, to 30 June
1998, of the **23,570 people who made their first ever purchase there during Q1 1997**.

That last part is the reason to use it. In most transaction datasets you cannot tell
whether a customer appearing in month one is new or has been buying for years — the data
is *left-censored*. Here, every customer's first purchase is inside the file, so "months
since first purchase" is a real quantity rather than an approximation.

Four columns, no header: customer ID, date, number of CDs, dollar value.

**Be able to say:** "Every customer in the file was acquired in Q1 1997 and tracked for up
to 18 months, so retention is measured rather than estimated. That's unusual and it's why
I chose it."

---

## 2. The first real decision: a row is not an order

The raw file has 69,659 rows but only **67,591 orders**. 1,774 customer-days have more than
one row — the separate items of a single order.

```python
orders = (tx.groupby(["customer_id", "date"], as_index=False)
            .agg(cds=("cds", "sum"), value=("value", "sum"), lines=("value", "size")))
```

This matters because every behavioural metric depends on it:

| Measured from | Orders per customer | Average order value |
|---|---|---|
| `transactions` (wrong) | 2.96 | $35.89 |
| `orders` (right) | 2.87 | $36.99 |

The difference is small here — 2.6% of orders are multi-line — but the habit is what
counts. On a dataset where orders routinely contain five items, measuring frequency from
lines would be badly wrong.

I made the same decision in my e-commerce project, where a row is a product line on an
invoice. **Always establish the grain of the table before calculating anything.**

### The other decisions

- **255 exact duplicate rows (0.37%).** Ambiguous: either someone bought two identical
  items the same day, or the row was keyed twice. I kept them, because this is the
  published version of the dataset used in the literature and removing rows would make my
  totals incomparable with everyone else's. I measured the effect — 0.17% of revenue — so
  the decision is informed rather than assumed.
- **80 lines with a $0 value but at least one CD.** Probably promotions or replacements.
  Kept, because they are genuine activity and therefore count towards whether a customer
  was active in a month, but they add nothing to revenue.
- **No negative values and no zero-quantity lines,** so unlike the e-commerce dataset there
  are no returns or credit notes to separate out. Worth checking rather than assuming.

---

## 3. How the cohort table is built

### Step 1 — assign each customer to a cohort

The cohort is the month of the customer's **first** order, and it never changes.

```python
first = orders.groupby("customer_id").agg(first_order_date=("date", "min"))
first["cohort_month"] = first.first_order_date.dt.to_period("M").astype(str)
```

Three cohorts: January 1997 (7,846 customers), February (8,476), March (7,248).

### Step 2 — the month index

For every order, how many whole months after the customer's first order did it happen?

```python
orders["months_since_first"] = (
    (orders.date.dt.year - orders.first_order_date.dt.year) * 12
    + (orders.date.dt.month - orders.first_order_date.dt.month)
)
```

**Why not just subtract the dates and divide by 30?** Because months are not 30 days.
A customer who first bought on 31 January and bought again on 1 February is one *calendar*
month later but one *day* later. Both answers are defensible, but you have to pick one and
say which.

I use calendar months. It means month 0 is "the rest of the month they joined in", which
is why month 0 is 100% by definition and why month 1 is the first interesting number.

**Be able to say:** "I used whole calendar months, so month 0 is the acquisition month.
A day-based definition would give slightly different numbers and I'd have had to say so."

### Step 3 — count active customers per cohort per month

```sql
SELECT cohort_month, months_since_first, COUNT(DISTINCT customer_id) AS active_customers
FROM orders
GROUP BY cohort_month, months_since_first
```

`COUNT(DISTINCT customer_id)`, not `COUNT(*)` — a customer who ordered three times in a
month is one active customer, not three.

### Step 4 — divide by the cohort size

The denominator is always the **original** cohort size, not the number still active last
month. So retention in month 6 means "6% of everyone we acquired that month bought in
month 6", which is the question a manager is actually asking.

```sql
ROUND(100.0 * a.active_customers / s.cohort_customers, 2) AS retention_pct
```

---

## 4. The trap: ragged cohorts

**This is the part most tutorials get wrong, and the thing worth raising unprompted in an
interview.**

The data ends on 30 June 1998. So:

| Cohort | Last observable month index |
|---|---|
| January 1997 | 17 |
| February 1997 | 16 |
| March 1997 | 15 |

If you build the cohort table without thinking about this, the February and March cohorts
appear to have **zero** retention in their final months. They do not. Those months were
never observed.

That mistake makes older cohorts look better than newer ones, in every cohort analysis
ever built — and the conclusion "our newer customers are worse" is wrong and expensive.

Two things in this project handle it:

- `sql/03_cohort_retention.sql` returns a `fully_observed` flag per cell.
- Every cross-cohort comparison — charts, the website, the 15-month value figure — uses
  **months 0 to 15 only**, which all three cohorts have.

```sql
CASE WHEN a.months_since_first <= w.max_observable_month THEN 1 ELSE 0 END AS fully_observed
```

**Be able to say:** "Cohort tables are triangular, not rectangular. The newest cohort has
the fewest observable periods, so I cap every comparison at 15 months — what all three
cohorts have."

---

## 5. What "retention" means here (and what it does not)

CDNOW is not a subscription. Nobody cancels. So "retention" here means **placed an order
in that month**, nothing more.

Consequences, all of which belong in the write-up:

- A customer who buys in month 2 and again in month 9 is simply inactive in between. They
  have not churned and returned.
- Because of that, retention does not have to decline monotonically — and it does not. The
  curve flattens at around 7.4% and wobbles.
- **Nobody is ever marked as lost.** This is why the curve flattens rather than going to
  zero: there is a stable core of regulars who keep buying, and a large group who bought
  once and stopped, but the data never declares the second group dead.

Measuring *churn* properly would need either a subscription, or a modelling approach (the
Pareto/NBD model was built on exactly this dataset). That is beyond what this project
does, and saying so is better than implying the retention number means more than it does.

---

## 6. Each query, and what it is for

| File | Question | Technique worth knowing |
|---|---|---|
| `01_overview.sql` | How big is the customer base? | Aggregating the pre-built `customers` table |
| `02_purchase_frequency.sql` | How often do people buy? | `CASE WHEN` bands, `SUM(SUM(x)) OVER ()` for share of total |
| `03_cohort_retention.sql` | The cohort table | Two joins, the observability flag |
| `04_new_vs_returning_by_month.sql` | First vs repeat orders by month | `COUNT(DISTINCT CASE WHEN ... END)` |
| `05_customer_segments.sql` | Who are the valuable groups? | `CROSS JOIN` to a calculated median |
| `06_time_to_second_order.sql` | How fast do people come back? | `LEAD()`, `JULIANDAY()` |
| `07_revenue_concentration.sql` | How concentrated is revenue? | `NTILE(10)`, running `SUM() OVER (ORDER BY)` |
| `08_value_by_order_number.sql` | Does behaviour change with tenure? | `LEAD()` for drop-off |
| `09_cohort_cumulative_revenue.sql` | What is an acquired customer worth? | `SUM() OVER (PARTITION BY ... ORDER BY ...)` |
| `10_repeat_rate_by_cohort.sql` | Are the cohorts comparable? | Correlated subqueries |

### Three techniques worth being able to explain

**`LEAD()` instead of a self-join** (`06_time_to_second_order.sql`):

```sql
LEAD(date) OVER (PARTITION BY customer_id ORDER BY date) AS next_order_date
```

Looks at the next row in the same customer's history. The alternative is joining the
orders table to itself on customer ID and a row-number offset — which works but is slower
and much harder to read. `LAG()` is the same thing backwards.

**`JULIANDAY()` for date arithmetic in SQLite:**

```sql
CAST(JULIANDAY(next_order_date) - JULIANDAY(date) AS INTEGER) AS days_to_next
```

SQLite has no date type; dates are text. `JULIANDAY()` converts to a number of days so they
can be subtracted. In PostgreSQL you would just write `next_order_date - date`.

**A calculated threshold instead of a hard-coded one** (`05_customer_segments.sql`):

```sql
WITH repeat_median AS (
    SELECT total_value AS median_repeat_spend FROM customers WHERE orders > 1
    ORDER BY total_value LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM customers WHERE orders > 1)
)
... CROSS JOIN repeat_median m ... WHERE c.total_value < m.median_repeat_spend
```

The spend threshold is the median spend of repeat buyers, calculated by the query. A
hard-coded `150` would silently become wrong the moment the data changed. `CROSS JOIN`
attaches that single value to every row.

**Why bands and not a clustering algorithm?** With two useful variables — order count and
total spend — bands are easier to explain to a manager, reproducible next quarter, and give
the same answer every time. K-means would be more impressive and less useful, and I would
not be able to explain why a particular customer landed in a particular cluster.

---

## 7. How each headline figure is calculated

| Figure | Calculation | Where |
|---|---|---|
| Revenue per customer $106.08 | total revenue ÷ 23,570 customers | `01_overview.sql` |
| Repeat buyer rate 48.9% | customers with >1 order ÷ all customers | `01_overview.sql` |
| Month-1 retention 14.9% | active in month 1 ÷ cohort size, summed across cohorts | `04_export_for_website.py` |
| Settled retention 7.4% | active customers months 6–15 ÷ cohort-months, all cohorts | `04_export_for_website.py` |
| 15-month value $102.74 | all revenue in months 0–15 ÷ 23,570 | `04_export_for_website.py` |
| First order share 37.1% | $38.08 (month 0) ÷ $102.74 | `04_export_for_website.py` |
| Top decile 50.9% of revenue | `NTILE(10)` decile 1 revenue ÷ total | `07_revenue_concentration.sql` |
| Drop-off after first order 51.1% | (23,570 − 11,516) ÷ 23,570 | `08_value_by_order_number.sql` |

### A bug I had to fix in my own code

The "second order within 3 months" figure was wrong first time. I wrote:

```python
second[second.time_to_second_order <= "c."]        # wrong
```

The band labels are `"a. Within 1 month"`, `"b. 1-2 months"`, `"c. 2-3 months"`. That is a
**string** comparison, and `"c. 2-3 months" <= "c."` is `False` because the longer string
sorts after the shorter one. So the `c.` band was silently dropped and the figure came out
as 51.5% instead of 59.8%.

```python
second[second.time_to_second_order.str.startswith(("a.", "b.", "c."))]   # right
```

**The lesson:** sorting prefixes like `a.`, `b.`, `c.` are great for ordering output and
dangerous for filtering. I only caught it because 35.7 + 15.8 + 8.3 obviously does not
equal 51.5 — which is a good argument for sanity-checking totals by hand.

---

## 8. Why each chart exists

| Chart | Question it answers | Design decision |
|---|---|---|
| `01_retention_curves.png` | How fast do customers go quiet? | Month 0 is excluded. Including a 100% point would squash the entire interesting range into the bottom tenth of the axis. |
| `02_retention_heatmap.png` | Do the cohorts differ? | The classic cohort grid, capped at month 15 so there are no misleading blanks. |
| `03_cumulative_revenue_per_customer.png` | What is an acquired customer worth over time? | The chart I would show a manager first. The denominator includes customers who never returned. |
| `04_purchase_frequency.png` | Where does revenue sit? | Paired bars: % of customers against % of revenue. The gap *is* the finding. |
| `05_revenue_concentration.png` | How concentrated is revenue? | Bars for each decile plus a cumulative line, so you can read "top 20% = 68%" directly. |
| `06_time_to_second_order.png` | When should a follow-up be sent? | Bands, because the exact day distribution is noisy and unactionable. |
| `07_dropoff_by_order_number.png` | Does loyalty compound? | Two axes: drop-off falls while order value rises. Both parts of one story. |
| `08_monthly_revenue_split.png` | What does a fixed base of customers produce? | Stacked, with a note explaining that no new customers appear after March 1997 by construction. |
| `09_customer_segments.png` | Who matters? | Horizontal bars, because segment names are long. |

I deliberately did not build a pie chart of segments. Comparing shares of customers against
shares of revenue needs two values per category, which a pie cannot show.

---

## 9. Likely interview questions

**"Explain cohort analysis to someone who has not heard of it."**
Group customers by when they first bought, then track each group forward in time. It
separates "we are losing customers" from "we acquired fewer customers", which a total
revenue chart mixes together.

**"What is the trap in building a cohort table?"**
Ragged edges. The newest cohort has the fewest observable periods, so its later months look
like zero retention when they were simply never observed. I flag observability per cell and
cap all comparisons at 15 months.

**"Why is month 0 always 100%?"**
Because the cohort is defined by buying in that month. It carries no information, which is
why I leave it off the retention chart.

**"Your retention flattens at about 7%. Is that good?"**
I can't say without a benchmark, and I don't have one. What I can say is that it is
*stable* — it stops declining from about month six — and identical across all three
cohorts, so it is a property of the business and not a blip.

**"How would you measure churn here?"**
I wouldn't, directly. There is no subscription, so nobody cancels. A customer is just
inactive, and might come back. Properly separating "gone" from "quiet" needs a model —
the Pareto/NBD was developed on this dataset — and that is beyond what I built.

**"Half the customers never came back. Is that bad?"**
It is normal for retail, and the more useful framing is what it is worth. Those customers
are 51.1% of the base and 14.7% of revenue. The gap between a 51.1% drop-off after the
first order and 29.5% after the third is where the opportunity is.

**"What's an acquired customer worth?"**
$102.74 over 15 months, including everyone who never returned. The first order is $38.08
of it. That difference is the whole argument for spending on retention.

**"How would you turn this into a target?"**
I wouldn't, from this data alone. There is no acquisition cost and no margin, so I can
describe the pattern but not say what it is worth spending to improve it. I'd ask for CAC
and gross margin by product before putting a number on any recommendation.

**"Why didn't you cluster the customers?"**
Two variables that a manager can act on — frequency and spend — are better served by bands.
Bands are explainable, reproducible, and I can say exactly why any customer is in any
group. K-means would look more sophisticated and be harder to use.

---

## 10. Exercises

### Beginner

1. Run `01_overview.sql`. Now run the same thing against `transactions` instead of
   `orders`. Which numbers change, and why?
2. How many customers placed exactly two orders? What share of revenue is that?
3. Which calendar month had the most active customers? Explain why it is not a surprise.
4. Find the single highest-spending customer. How many orders, over how long?

### Intermediate

5. Rebuild the retention table using **90-day periods** instead of calendar months. Does
   the shape of the curve change?
6. Change `05_customer_segments.sql` to use the 75th percentile instead of the median as
   the spend threshold. How do the segment sizes move?
7. Calculate retention using "ordered in month m **or any later month**" instead of
   "ordered in month m". Why is that curve so much higher, and which definition answers
   which question?
8. For customers whose second order came within 30 days, what is their average lifetime
   spend? Compare with those who took over 90 days. What would you do with that?

### Harder

9. Build a cohort table of **cumulative orders per customer** instead of revenue. At what
   month does the average acquired customer reach two orders?
10. The retention curve flattens at about 7.4%. Estimate how many customers make up that
    steady core, and check your estimate against `02_purchase_frequency.sql`.
11. Split the retention curves by whether the customer's first order was above or below
    the median first-order value. Does a bigger first order predict better retention?
12. Rewrite `03_cohort_retention.sql` so the observability window is calculated from the
    data (`MAX(date)` in the orders table) rather than hard-coded in a `CASE` statement.
    This is how it should work on a dataset that gets updated.

---

## 11. Things I would do differently next time

- **Write the observability check before the chart, not after.** I built the first
  retention chart without it and spent a while confused by a cliff at the right-hand edge
  that turned out to be missing data.
- **Sanity-check percentages by hand.** The string-comparison bug in section 7 would have
  survived if I had not noticed that three numbers did not add up.
- **Decide what "an order" is on day one.** Everything downstream depends on it, and
  changing it later means re-running everything.
