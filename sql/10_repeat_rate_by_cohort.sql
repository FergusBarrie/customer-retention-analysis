-- 10_repeat_rate_by_cohort.sql
-- Were the three acquisition cohorts equally good?
--
-- All three were acquired within three months of each other, so I would expect
-- them to look similar. Checking is worth the two minutes: if one cohort
-- behaves differently, that usually points to a promotion or a channel that
-- brought in a different kind of customer.
--
-- To keep the comparison fair, the last two columns measure each cohort over
-- its first 15 months only, because that is all the March 1997 cohort has.

WITH per_customer AS (
    SELECT
        c.cohort_month,
        c.customer_id,
        c.orders,
        c.total_value,
        c.is_repeat_buyer,
        -- orders and revenue within the first 15 months of the relationship
        (SELECT COUNT(*) FROM orders o
          WHERE o.customer_id = c.customer_id AND o.months_since_first <= 15) AS orders_15m,
        (SELECT COALESCE(SUM(o.value), 0) FROM orders o
          WHERE o.customer_id = c.customer_id AND o.months_since_first <= 15) AS revenue_15m
    FROM customers c
)
SELECT
    cohort_month,
    COUNT(*)                                          AS cohort_customers,
    SUM(is_repeat_buyer)                              AS repeat_buyers,
    ROUND(100.0 * SUM(is_repeat_buyer) / COUNT(*), 1) AS repeat_buyer_pct,
    ROUND(AVG(orders), 2)                             AS avg_orders_all_time,
    ROUND(AVG(total_value), 2)                        AS avg_revenue_all_time,
    ROUND(AVG(orders_15m), 2)                         AS avg_orders_first_15_months,
    ROUND(AVG(revenue_15m), 2)                        AS avg_revenue_first_15_months
FROM per_customer
GROUP BY cohort_month
ORDER BY cohort_month;
