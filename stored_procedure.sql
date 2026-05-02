DELIMITER //
CREATE PROCEDURE calculate_portfolio_pnl(IN p_portfolio_id INT)
BEGIN
SELECT
s.symbol,
h.shares,
h.buy_price,
dp.close_price AS current_price,
ROUND(h.shares * (dp.close_price - h.buy_price), 2) AS profit_loss,
ROUND((dp.close_price - h.buy_price)
/ h.buy_price * 100, 2) AS return_pct
FROM holdings h
JOIN stocks s ON s.stock_id = h.stock_id
JOIN daily_prices dp ON dp.stock_id = h.stock_id
AND dp.price_date = (SELECT MAX(price_date) FROM daily_prices)
WHERE h.portfolio_id = p_portfolio_id
ORDER BY return_pct DESC;
END //
DELIMITER ;

-- to call stored procedure
CALL calculate_portfolio_pnl(1);