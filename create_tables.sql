CREATE TABLE stocks (
stock_id INT AUTO_INCREMENT PRIMARY KEY,
symbol VARCHAR(10) NOT NULL UNIQUE,
company_name VARCHAR(100) NOT NULL,
sector VARCHAR(50)
);

CREATE TABLE daily_prices (
price_id INT AUTO_INCREMENT PRIMARY KEY,
stock_id INT NOT NULL,
price_date DATE NOT NULL,
open_price DECIMAL(10,2),
close_price DECIMAL(10,2) NOT NULL,
volume BIGINT,
FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
UNIQUE KEY uq_stock_date (stock_id, price_date)
);

CREATE TABLE portfolio (
portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
owner_name VARCHAR(100),
created_at DATE DEFAULT (CURDATE())
);

CREATE TABLE holdings (
holding_id INT AUTO_INCREMENT PRIMARY KEY,
portfolio_id INT NOT NULL,
stock_id INT NOT NULL,
shares DECIMAL(10,4) NOT NULL,
buy_price DECIMAL(10,2) NOT NULL,
buy_date DATE NOT NULL,
FOREIGN KEY (portfolio_id) REFERENCES portfolio(portfolio_id),
FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);