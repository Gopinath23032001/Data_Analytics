WITH daily_returns AS (
SELECT
dp.stock_id,
s.symbol,
(dp.close_price
- LAG(dp.close_price) OVER (PARTITION BY dp.stock_id ORDER BY dp.price_date))
/ LAG(dp.close_price) OVER (PARTITION BY dp.stock_id ORDER BY dp.price_date)
AS daily_ret
FROM daily_prices dp
JOIN stocks s ON s.stock_id = dp.stock_id
)
SELECT
symbol,
ROUND(STDDEV(daily_ret) * 100, 4) AS volatility_pct,
RANK() OVER (ORDER BY STDDEV(daily_ret) DESC) AS volatility_rank
FROM daily_returns
WHERE daily_ret IS NOT NULL
GROUP BY stock_id, symbol
ORDER BY volatility_rank;