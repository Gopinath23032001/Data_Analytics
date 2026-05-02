CREATE VIEW portfolio_summary AS
WITH latest_price AS (
SELECT stock_id, close_price AS current_price
FROM daily_prices
WHERE price_date = (SELECT MAX(price_date) FROM daily_prices)
)
SELECT
s.symbol, s.company_name, s.sector,
h.shares, h.buy_price, h.buy_date,
lp.current_price,
ROUND(h.shares * lp.current_price, 2) AS current_value,
ROUND(h.shares * (lp.current_price - h.buy_price), 2) AS profit_loss,
ROUND((lp.current_price - h.buy_price)
/ h.buy_price * 100, 2) AS return_pct
FROM holdings h
JOIN stocks s ON s.stock_id = h.stock_id
JOIN latest_price lp ON lp.stock_id = h.stock_id;

-- to check whether views is created 
SELECT * FROM portfolio_summary ORDER BY return_pct DESC;
