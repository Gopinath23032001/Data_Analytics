WITH stock_returns AS (
SELECT
s.symbol, s.sector,
ROUND((MAX(dp.close_price) - MIN(dp.close_price))
/ MIN(dp.close_price) * 100, 2) AS total_return_pct
FROM daily_prices dp
JOIN stocks s ON s.stock_id = dp.stock_id
WHERE YEAR(dp.price_date) = 2024
GROUP BY s.stock_id, s.symbol, s.sector
)
SELECT
symbol, sector, total_return_pct,
NTILE(4) OVER (ORDER BY total_return_pct DESC) AS quartile
FROM stock_returns
ORDER BY total_return_pct DESC;