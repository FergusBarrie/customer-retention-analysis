-- 09_cohort_cumulative_revenue.sql
-- Cumulative revenue per acquired customer, by months since their first order.
--
-- This is the chart I would show a manager first. It answers: "if we acquire a
-- customer today, how much have they been worth to us after 3, 6 or 12
-- months?" The denominator is always the full cohort, including the customers
-- who never came back, because those are part of what an acquired customer is
-- worth on average.
--
-- SUM(...) OVER (PARTITION BY cohort ORDER BY month) gives the running total
-- within each cohort.

WITH cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers
    FROM customers
    GROUP BY cohort_month
),
monthly AS (
    SELECT cohort_month, months_since_first, ROUND(SUM(value), 2) AS revenue
    FROM orders
    GROUP BY cohort_month, months_since_first
)
SELECT
    m.cohort_month,
    m.months_since_first,
    s.cohort_customers,
    m.revenue,
    ROUND(m.revenue / s.cohort_customers, 2) AS revenue_per_customer,
    ROUND(SUM(m.revenue) OVER (PARTITION BY m.cohort_month ORDER BY m.months_since_first), 2)
        AS cumulative_revenue,
    ROUND(SUM(m.revenue) OVER (PARTITION BY m.cohort_month ORDER BY m.months_since_first)
          / s.cohort_customers, 2) AS cumulative_revenue_per_customer
FROM monthly m
JOIN cohort_size s ON m.cohort_month = s.cohort_month
ORDER BY m.cohort_month, m.months_since_first;
