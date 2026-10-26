# Findings — Customer Behaviour and Retention Analysis

**Business question:** Of the customers this retailer acquired, how many came back, how
quickly did activity fall away, and how much is an acquired customer actually worth?

The dataset is the complete purchase history, to 30 June 1998, of the 23,570 people who
made their first ever purchase at the online CD retailer CDNOW during the first quarter of
1997. Every customer is tracked from their first order, so retention here is measured
rather than estimated.

---

## 1. The customer base at a glance

`outputs/tables/01_overview.csv`

| Metric | Value |
|---|---|
| Customers | 23,570 |
| Orders | 67,591 |
| Revenue | $2,500,316 |
| Average order value | $36.99 |
| Revenue per customer (over 18 months) | $106.08 |
| Average orders per customer | 2.87 |
| Customers with more than one order | 11,516 (48.9%) |

An order is one customer on one day. The raw file has 69,659 transaction *lines*; 2.6% of
orders contain more than one line. Measuring frequency from lines would overstate how often
people bought.

---

## 2. Half the customers never came back — and they are a seventh of revenue

`outputs/tables/02_purchase_frequency.csv`

| Orders placed | Customers | % of customers | Revenue | % of revenue | Avg per customer |
|---|---|---|---|---|---|
| 1 | 12,054 | **51.1%** | $367,602 | **14.7%** | $30.50 |
| 2 | 4,040 | 17.1% | $270,130 | 10.8% | $66.86 |
| 3 | 2,205 | 9.4% | $229,597 | 9.2% | $104.13 |
| 4–5 | 2,427 | 10.3% | $389,201 | 15.6% | $160.36 |
| 6–10 | 1,952 | 8.3% | $559,105 | 22.4% | $286.43 |
| 11+ | 892 | **3.8%** | $684,681 | **27.4%** | $767.58 |

Both ends of this table matter. Half the customer base bought once and produced under a
seventh of revenue. At the other end, 892 customers — 3.8% — produced more than a quarter
of it.

Revenue concentration confirms it (`07_revenue_concentration.csv`): the top-spending
**10% of customers produced 50.9% of revenue**, averaging $540 each. The top 20% produced
67.7%. The bottom half of the customer base produced about 10%.

---

## 3. Retention falls off a cliff, then holds steady

`outputs/tables/cohort_retention_matrix.csv` — share of each cohort placing an order in
each month after their first purchase.

| Cohort | M0 | M1 | M2 | M3 | M4 | M5 | M6 | M9 | M12 | M15 |
|---|---|---|---|---|---|---|---|---|---|---|
| Jan 1997 | 100% | 14.8% | 12.3% | 10.3% | 8.7% | 9.4% | 9.2% | 7.6% | 6.7% | 6.0% |
| Feb 1997 | 100% | 15.5% | 11.6% | 9.2% | 10.0% | 9.3% | 7.4% | 8.5% | 6.7% | 6.5% |
| Mar 1997 | 100% | 14.2% | 10.4% | 10.4% | 9.3% | 7.8% | 7.7% | 7.8% | 9.4% | 6.3% |

Month 0 is 100% by definition — the cohort is defined by buying in that month.

Two things to take from this. First, the drop is immediate: only about **14.9%** of a
cohort bought again in the following month. Second, and more interesting, **the curve then
flattens**. From month six onwards it settles at around **7.4%** active in any given month
and stays there rather than continuing to decay.

So this is not a business steadily bleeding customers. It is a business with a small,
stable core of regulars and a large group who bought once and never returned. Those two
groups are visible in section 2 as the 3.8% and the 51.1%.

A caveat on language: CDNOW is not a subscription, so nobody cancels. "Retention" here
means *placed an order that month*. A customer inactive in month 7 and active in month 9
has not churned and returned — they were just quiet. Nobody in this data is ever marked as
lost.

---

## 4. The three cohorts behave almost identically

`outputs/tables/10_repeat_rate_by_cohort.csv`

| Cohort | Customers | Repeat buyer rate | Avg orders (15m) | Avg revenue (15m) |
|---|---|---|---|---|
| Jan 1997 | 7,846 | 49.3% | 2.83 | $106.51 |
| Feb 1997 | 8,476 | 48.1% | 2.78 | $101.38 |
| Mar 1997 | 7,248 | 49.2% | 2.73 | $100.24 |

Repeat rates within 1.2 percentage points of each other, revenue per customer within $6.27.

This is a boring table and an important one. It means the retention curve is a stable
property of this business, not an artifact of one month's intake. If one cohort had looked
different, the first thing to check would be whether a promotion that month brought in a
different kind of customer.

The comparison uses the first 15 months for all three, because that is all the March cohort
has — see the note on ragged cohorts below.

---

## 5. The first order is about a third of what a customer is worth

`outputs/tables/cohort_cumulative_revenue_matrix.csv` — cumulative revenue per *acquired*
customer, including everyone who never came back.

| Months since first order | 0 | 3 | 6 | 9 | 12 | 15 |
|---|---|---|---|---|---|---|
| Jan 1997 cohort | $38.12 | $57.54 | $71.61 | $82.98 | $95.75 | $106.51 |
| Feb 1997 cohort | $37.58 | $55.30 | $68.64 | $80.51 | $90.94 | $101.38 |
| Mar 1997 cohort | $38.62 | $55.59 | $68.06 | $80.50 | $91.86 | $100.24 |

Across all three cohorts, an acquired customer was worth **$102.74** over 15 months, of
which **$38.08 (37.1%)** came from the first order.

The remaining 63% depended entirely on the customer coming back. The practical consequence
is in the recommendations: judging an acquisition channel on the first order alone
undervalues it by roughly two thirds.

The curve is also close to linear after the first couple of months, adding roughly $3.50 to
$4.50 per acquired customer per month, with no sign of flattening within 15 months.

---

## 6. Each order makes the next one more likely — and larger

`outputs/tables/08_value_by_order_number.csv`

| Order number | Customers reaching it | % who never placed the next | Avg order value |
|---|---|---|---|
| 1 | 23,570 | **51.1%** | $33.29 |
| 2 | 11,516 | 35.1% | $36.05 |
| 3 | 7,476 | **29.5%** | $36.83 |
| 5 | 3,835 | 25.8% | $39.08 |
| 10 | 1,074 | **16.9%** | $43.30 |

Both columns move in the customer's favour. The chance of stopping falls from 51.1% after
the first order to about 17% by the tenth, while average order value rises 30%, from $33.29
to $43.30.

**One honest caveat.** Customers who reach a tenth order are the keenest buyers by
definition, so part of the rise in order value is selection rather than customers genuinely
spending more over time. This dataset cannot separate the two. The drop-off column is less
affected and is the more reliable half of the finding.

---

## 7. If customers come back, they come back quickly

`outputs/tables/06_time_to_second_order.csv`

| Time to second order | Repeat buyers | % of repeat buyers |
|---|---|---|
| Within 1 month | 4,115 | **35.7%** |
| 1–2 months | 1,814 | 15.8% |
| 2–3 months | 958 | 8.3% |
| 3–6 months | 1,940 | 16.8% |
| 6–12 months | 1,983 | 17.2% |
| Over 12 months | 706 | 6.1% |

**59.8%** of all second orders happened within three months, and 35.7% within a single
month. The median repeat buyer came back in well under two months.

This is the most directly usable number in the project: it tells you when a follow-up is
still timely. A reactivation email at six months is mostly reaching people who have already
gone.

---

## 8. Customer segments

`outputs/tables/05_customer_segments.csv`. The spend threshold is the median total spend of
repeat buyers, calculated by the query rather than hard-coded.

| Segment | Customers | % of customers | Revenue | % of revenue | Avg revenue |
|---|---|---|---|---|---|
| Best customers (4+ orders, higher spend) | 4,356 | 18.5% | $1,561,548 | **62.5%** | $358.48 |
| One-time buyer | 12,054 | 51.1% | $367,602 | 14.7% | $30.50 |
| Light repeat (2–3 orders, lower spend) | 4,843 | 20.5% | $257,543 | 10.3% | $53.18 |
| Occasional, higher value (2–3 orders) | 1,402 | 5.9% | $242,184 | 9.7% | $172.74 |
| Frequent, lower value (4+ orders) | 915 | 3.9% | $71,439 | 2.9% | $78.08 |

18.5% of customers produce 62.5% of revenue, and they stay active for an average of 382
days against 0 for one-time buyers.

---

## Recommendations

**1. Concentrate on the second order, and do it in the first month.**
The first-to-second-order step is where 51.1% of customers are lost — against 29.5% after
a third order. And the timing is unambiguous: 35.7% of all second orders come within a
month and 59.8% within three. A follow-up programme aimed at the first four to six weeks
addresses the largest break point at the moment it is still open.

**2. Judge acquisition on the 15-month figure, not the first order.**
An acquired customer is worth $102.74 over 15 months, not the $38.08 of their first
purchase. A channel that looks marginal against the first order may be comfortably
worthwhile against the full figure. This analysis gives a defensible number to use in that
comparison.

**3. Measure the top decile separately.**
2,357 customers averaging $540 each produce half of all revenue. Whether that group is
growing or shrinking is the single most important thing about this business, and total
revenue would hide it. At minimum it should be a tracked number.

**I have deliberately not attached a monetary value to any of these.** The dataset contains
no acquisition costs, no marketing spend and no product margin, so any claim about return
on investment would be invented. What the data supports is where the opportunity is and how
large the groups are.

## Limitations

1. **The data is from 1997–98.** The method transfers; the percentages are not benchmarks
   for a modern business.
2. **Only customer, date, quantity and value.** No product, channel, marketing or
   demographic data, so this describes *what* customers did and never *why*.
3. **No acquisition cost and no margin,** so nothing here can be turned into a return on
   investment.
4. **Three cohorts, one quarter.** No way to see seasonality or a trend in acquisition
   quality.
5. **Comparisons are capped at 15 months.** The data ends in June 1998, so the January
   cohort has 17 observable months, February 16 and March 15. Ignoring this would make the
   later cohorts look artificially worse — the single most common error in cohort analysis.
6. **"Retention" means ordering in a given month,** not the opposite of cancelling.
   Customers are never marked as lost, which is part of why the curve flattens instead of
   falling to zero.
7. **Order-number figures are affected by survivorship.** Customers who reach a tenth order
   are the keenest buyers by definition.
8. **255 duplicate rows (0.37%) were kept,** worth 0.17% of revenue. No conclusion depends
   on the choice.
