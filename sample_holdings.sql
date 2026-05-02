INSERT INTO portfolio (owner_name) VALUES ('Gopi Portfolio');

INSERT INTO holdings (portfolio_id, stock_id, shares, buy_price, buy_date)
SELECT 1, stock_id, 10, 150.00, '2022-06-01' FROM stocks WHERE symbol='AAPL'
UNION ALL
SELECT 1, stock_id, 5, 280.00, '2022-06-01' FROM stocks WHERE symbol='MSFT'
UNION ALL
SELECT 1, stock_id, 8, 200.00, '2022-06-01' FROM stocks WHERE symbol='GOOGL'
UNION ALL
SELECT 1, stock_id, 3, 700.00, '2022-06-01' FROM stocks WHERE symbol='TSLA'
UNION ALL
SELECT 1, stock_id, 4, 115.00, '2022-06-01' FROM stocks WHERE symbol='NVDA';