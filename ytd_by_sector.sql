SELECT
    s.sector,
    COUNT(DISTINCT s.stock_id) AS num_stocks,
    ROUND(AVG(
        (p_end.close_price - p_start.close_price)
        / p_start.close_price * 100
    ), 2) AS avg_ytd_return_pct
FROM stocks s
JOIN daily_prices p_start ON s.stock_id = p_start.stock_id
    AND p_start.price_date = (
        SELECT MIN(price_date) FROM daily_prices
        WHERE YEAR(price_date) = 2024
    )
JOIN daily_prices p_end ON s.stock_id = p_end.stock_id
    AND p_end.price_date = (SELECT MAX(price_date) FROM daily_prices)
GROUP BY s.sector
ORDER BY avg_ytd_return_pct DESC;