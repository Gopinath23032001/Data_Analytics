SELECT
s.symbol,
dp.price_date,
dp.close_price,
ROUND(AVG(dp.close_price) OVER (
PARTITION BY dp.stock_id
ORDER BY dp.price_date
ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
), 2) AS moving_avg_30d
FROM daily_prices dp
JOIN stocks s ON s.stock_id = dp.stock_id
ORDER BY s.symbol, dp.price_date;