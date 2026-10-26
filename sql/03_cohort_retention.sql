-- 03_cohort_retention.sql
-- The cohort retention table: of the customers acquired in a given month,
-- what share placed an order in each later month?
--
-- How it works
--   `months_since_first` is 0 in the month a customer first bought, 1 in the
--   following month and so on. It is calculated during cleaning as
--   (year difference x 12) + month difference.
--   A customer counts as active in month m if they placed at least one order
--   in that month. Month 0 is 100% by definition - everyone bought in the
--   month they were acquired.
--
-- The thing that is easy to get wrong
--   The data ends on 30 June 1998. The January 1997 cohort can therefore be
--   observed for 17 months, February's for 16 and March's for 15. If you
--   ignore that, the later months of the February and March cohorts look like
--   zero retention when in fact they were simply not observed.
--   The `fully_observed` column below flags which cells are safe to compare,
--   and the website chart only plots months 0-15 for all three cohorts.

WITH cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers
    FROM customers
    GROUP BY cohort_month
),
-- The last month index each cohort can possibly be observed for, given the
-- data ends in June 1998 (month index 17 for the January 1997 cohort).
cohort_window AS (
    SELECT cohort_month,
           CASE cohort_month WHEN '1997-01' THEN 17
                             WHEN '1997-02' THEN 16
                             WHEN '1997-03' THEN 15
           END AS max_observable_month
    FROM cohort_size
),
activity AS (
    SELECT
        cohort_month,
        months_since_first,
        COUNT(DISTINCT customer_id) AS active_customers,
        COUNT(*)                    AS orders,
        ROUND(SUM(value), 2)        AS revenue
    FROM orders
    GROUP BY cohort_month, months_since_first
)
SELECT
    a.cohort_month,
    a.months_since_first,
    s.cohort_customers,
    a.active_customers,
    a.orders,
    a.revenue,
    ROUND(100.0 * a.active_customers / s.cohort_customers, 2) AS retention_pct,
    ROUND(a.revenue / s.cohort_customers, 2)                  AS revenue_per_cohort_customer,
    CASE WHEN a.months_since_first <= w.max_observable_month THEN 1 ELSE 0 END AS fully_observed
FROM activity a
JOIN cohort_size s   ON a.cohort_month = s.cohort_month
JOIN cohort_window w ON a.cohort_month = w.cohort_month
ORDER BY a.cohort_month, a.months_since_first;
