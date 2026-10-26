-- 02_purchase_frequency.sql
-- How many orders does a customer place, and how is revenue spread across
-- those groups?
--
-- The bands are deliberately simple. The important comparison is between the
-- share of customers in a band and the share of revenue it produces.

WITH banded AS (
    SELECT
        customer_id,
        orders,
        total_value,
        CASE WHEN orders = 1               THEN '1 order'
             WHEN orders = 2               THEN '2 orders'
             WHEN orders = 3               THEN '3 orders'
             WHEN orders BETWEEN 4 AND 5   THEN '4-5 orders'
             WHEN orders BETWEEN 6 AND 10  THEN '6-10 orders'
             ELSE                               '11+ orders'
        END AS order_band,
        CASE WHEN orders = 1               THEN 1
             WHEN orders = 2               THEN 2
             WHEN orders = 3               THEN 3
             WHEN orders BETWEEN 4 AND 5   THEN 4
             WHEN orders BETWEEN 6 AND 10  THEN 5
             ELSE                               6
        END AS band_sort
    FROM customers
)
SELECT
    order_band,
    COUNT(*)                                           AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_customers,
    ROUND(SUM(total_value), 2)                         AS revenue,
    ROUND(100.0 * SUM(total_value) / SUM(SUM(total_value)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(total_value), 2)                         AS avg_revenue_per_customer
FROM banded
GROUP BY order_band, band_sort
ORDER BY band_sort;
