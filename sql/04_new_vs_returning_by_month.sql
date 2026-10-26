-- 04_new_vs_returning_by_month.sql
-- Each calendar month: how many customers were buying for the first time, how
-- many were coming back, and how the revenue split between them.
--
-- Because every customer in this dataset was acquired in the first quarter of
-- 1997, there are no new customers at all from April 1997 onwards. That is a
-- property of how the dataset was built, not a business collapse, and it is
-- worth saying clearly before anyone reads the chart as a failure to acquire.
--
-- What the months from April 1997 do show, very cleanly, is what a fixed group
-- of customers is worth over time with no new acquisition at all.

SELECT
    order_month,
    COUNT(DISTINCT CASE WHEN order_number = 1 THEN customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN order_number > 1 THEN customer_id END) AS returning_customers,
    COUNT(DISTINCT customer_id)                                     AS active_customers,
    SUM(CASE WHEN order_number = 1 THEN 1 ELSE 0 END)               AS first_orders,
    SUM(CASE WHEN order_number > 1 THEN 1 ELSE 0 END)               AS repeat_orders,
    ROUND(SUM(CASE WHEN order_number = 1 THEN value ELSE 0 END), 2) AS new_customer_revenue,
    ROUND(SUM(CASE WHEN order_number > 1 THEN value ELSE 0 END), 2) AS returning_customer_revenue,
    ROUND(SUM(value), 2)                                            AS total_revenue,
    ROUND(SUM(value) / COUNT(*), 2)                                 AS avg_order_value
FROM orders
GROUP BY order_month
ORDER BY order_month;
