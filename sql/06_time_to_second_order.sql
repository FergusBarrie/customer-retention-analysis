-- 06_time_to_second_order.sql
-- For customers who came back, how long did it take?
--
-- This is the most actionable number in the whole project: it tells you when a
-- follow-up would still be timely and when a customer has probably already
-- gone.
--
-- LEAD() is the window function doing the work. It looks at the NEXT row in
-- the same customer's order history, so I can subtract one date from the next
-- without a self-join. JULIANDAY() is how SQLite does date arithmetic - it
-- converts a date to a number of days so the two can be subtracted.

WITH with_next AS (
    SELECT
        customer_id,
        order_number,
        date,
        LEAD(date) OVER (PARTITION BY customer_id ORDER BY date) AS next_order_date
    FROM orders
),
gaps AS (
    SELECT
        customer_id,
        CAST(JULIANDAY(next_order_date) - JULIANDAY(date) AS INTEGER) AS days_to_next
    FROM with_next
    WHERE order_number = 1            -- only the gap from the first to the second order
      AND next_order_date IS NOT NULL -- customers who never came back have no gap
)
SELECT
    CASE WHEN days_to_next <= 30   THEN 'a. Within 1 month'
         WHEN days_to_next <= 60   THEN 'b. 1-2 months'
         WHEN days_to_next <= 90   THEN 'c. 2-3 months'
         WHEN days_to_next <= 180  THEN 'd. 3-6 months'
         WHEN days_to_next <= 365  THEN 'e. 6-12 months'
         ELSE                           'f. Over 12 months'
    END                                                AS time_to_second_order,
    COUNT(*)                                           AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_repeat_buyers,
    ROUND(AVG(days_to_next), 0)                        AS avg_days_in_band
FROM gaps
GROUP BY time_to_second_order
ORDER BY time_to_second_order;
