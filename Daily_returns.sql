SELECT
s.symbol,
dp.price_date,
dp.close_price,
LAG(dp.close_price) OVER (
PARTITION BY dp.stock_id ORDER BY dp.price_date
) AS prev_close,
ROUND(
(dp.close_price
- LAG(dp.close_price) OVER (PARTITION BY dp.stock_id ORDER BY dp.price_date))
/ LAG(dp.close_price) OVER (PARTITION BY dp.stock_id ORDER BY dp.price_date)
* 100, 2
) AS daily_return_pct
FROM daily_prices dp
JOIN stocks s ON s.stock_id = dp.stock_id
ORDER BY s.symbol, dp.price_date;