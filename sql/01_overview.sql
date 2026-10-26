-- 01_overview.sql
-- Headline numbers for the whole customer base.
--
-- Note which table each figure comes from. Orders come from the `orders`
-- table (one row per customer per day), not from `transactions` (one row per
-- line). Counting lines would overstate how often people bought.

SELECT
    COUNT(*)                                            AS customers,
    SUM(orders)                                         AS orders,
    ROUND(SUM(total_value), 2)                          AS revenue,
    ROUND(SUM(total_value) / SUM(orders), 2)            AS avg_order_value,
    ROUND(SUM(total_value) / COUNT(*), 2)               AS revenue_per_customer,
    ROUND(1.0 * SUM(orders) / COUNT(*), 2)              AS avg_orders_per_customer,
    SUM(is_repeat_buyer)                                AS repeat_buyers,
    ROUND(100.0 * SUM(is_repeat_buyer) / COUNT(*), 1)   AS repeat_buyer_pct,
    MIN(first_order_date)                               AS first_acquisition,
    MAX(last_order_date)                                AS last_activity
FROM customers;
