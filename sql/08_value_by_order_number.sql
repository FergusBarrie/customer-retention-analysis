-- 08_value_by_order_number.sql
-- Does a customer's order get bigger the more often they buy?
--
-- For each order number (first order, second order, third...), the average
-- order value and how many customers ever got that far. The drop-off column is
-- the share of customers who placed order N but never placed order N+1, which
-- is a per-order version of churn.
--
-- Careful with this one: customers who reach a tenth order are not a random
-- sample - they are the keenest buyers by definition. So a rising average
-- order value here is partly a real effect and partly survivorship. The
-- write-up says so.

WITH per_order AS (
    SELECT
        order_number,
        COUNT(*)                   AS orders_placed,
        ROUND(AVG(value), 2)       AS avg_order_value,
        ROUND(AVG(cds), 2)         AS avg_cds,
        ROUND(SUM(value), 2)       AS revenue
    FROM orders
    GROUP BY order_number
)
SELECT
    order_number,
    orders_placed                                              AS customers_reaching_this_order,
    avg_order_value,
    avg_cds,
    revenue,
    LEAD(orders_placed) OVER (ORDER BY order_number)           AS customers_reaching_next_order,
    ROUND(100.0 * (orders_placed - LEAD(orders_placed) OVER (ORDER BY order_number))
          / orders_placed, 1)                                  AS drop_off_pct
FROM per_order
WHERE order_number <= 12
ORDER BY order_number;
