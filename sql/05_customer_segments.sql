-- 05_customer_segments.sql
-- Group customers by how often they bought and how much they spent.
--
-- These segments are deliberately simple and based on two things a manager can
-- act on: how many times someone bought, and what they were worth. I avoided a
-- clustering algorithm on purpose - with two useful variables, bands are easier
-- to explain, easier to reproduce next quarter, and give the same answer.
--
-- The spend threshold is the median total spend of repeat buyers, which the
-- query calculates rather than hard-codes, so the segments stay sensible if
-- the data changes.

WITH repeat_median AS (
    SELECT total_value AS median_repeat_spend
    FROM customers
    WHERE orders > 1
    ORDER BY total_value
    LIMIT 1
    OFFSET (SELECT COUNT(*) / 2 FROM customers WHERE orders > 1)
),
segmented AS (
    SELECT
        c.customer_id,
        c.orders,
        c.total_value,
        c.customer_lifespan_days,
        CASE
            WHEN c.orders = 1                                       THEN 'One-time buyer'
            WHEN c.orders BETWEEN 2 AND 3
                 AND c.total_value < m.median_repeat_spend          THEN 'Light repeat'
            WHEN c.orders BETWEEN 2 AND 3                           THEN 'Occasional, higher value'
            WHEN c.orders >= 4
                 AND c.total_value < m.median_repeat_spend          THEN 'Frequent, lower value'
            ELSE                                                         'Best customers'
        END AS segment
    FROM customers c
    CROSS JOIN repeat_median m
)
SELECT
    segment,
    COUNT(*)                                            AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_customers,
    ROUND(SUM(total_value), 2)                          AS revenue,
    ROUND(100.0 * SUM(total_value) / SUM(SUM(total_value)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(total_value), 2)                          AS avg_revenue_per_customer,
    ROUND(AVG(orders), 2)                               AS avg_orders,
    ROUND(AVG(customer_lifespan_days), 0)               AS avg_days_first_to_last_order
FROM segmented
GROUP BY segment
ORDER BY revenue DESC;
