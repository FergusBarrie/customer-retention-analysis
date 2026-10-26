-- 07_revenue_concentration.sql
-- Split customers into ten equal groups by total spend and show how much
-- revenue each group produced.
--
-- NTILE(10) does the splitting: it orders customers by spend and assigns them
-- to ten buckets of equal SIZE (about 2,357 customers each), which is what
-- makes the revenue shares comparable.
--
-- The cumulative column uses a running SUM() OVER (ORDER BY ...), so the first
-- row answers "what share of revenue comes from the top 10% of customers".

WITH deciles AS (
    SELECT
        customer_id,
        orders,
        total_value,
        NTILE(10) OVER (ORDER BY total_value DESC) AS spend_decile
    FROM customers
),
by_decile AS (
    SELECT
        spend_decile,
        COUNT(*)                   AS customers,
        ROUND(SUM(total_value), 2) AS revenue,
        ROUND(AVG(total_value), 2) AS avg_spend,
        ROUND(AVG(orders), 2)      AS avg_orders,
        ROUND(MIN(total_value), 2) AS min_spend,
        ROUND(MAX(total_value), 2) AS max_spend
    FROM deciles
    GROUP BY spend_decile
)
SELECT
    spend_decile,
    customers,
    revenue,
    avg_spend,
    avg_orders,
    min_spend,
    max_spend,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 1)                      AS pct_of_revenue,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY spend_decile)
          / SUM(revenue) OVER (), 1)                                      AS cumulative_pct_of_revenue
FROM by_decile
ORDER BY spend_decile;
