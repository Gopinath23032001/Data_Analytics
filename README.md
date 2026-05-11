# 📈 SQL Stock Portfolio Analysis System
> A SQL-based stock portfolio analysis system built with MySQL — demonstrates window functions, CTEs, stored procedures, and query optimization on real market data.

![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?logo=mysql) ![Status](https://img.shields.io/badge/Status-Complete-brightgreen) ![Queries](https://img.shields.io/badge/Queries-10%2B-orange)

---

## 📌 Project overview

This project builds a relational database to track and analyze stock portfolio performance. It answers real business questions using advanced SQL.

**Tools used:** MySQL 8.0 · MySQL Workbench · Python (yfinance)  
**Dataset:** 2 years of daily price data for 10 stocks (AAPL, MSFT, GOOGL, TSLA, AMZN, META, NVDA, JPM, JNJ, V)

---

## 🗂️ Folder structure

```
sql-stock-portfolio-analysis/
├── README.md
├── schema/
│   ├── create_tables.sql        # All 4 table definitions
│   └── erd_diagram.png          # Entity Relationship Diagram
├── data/
│   ├── load_stocks.sql          # Stock metadata INSERT statements
│   ├── sample_holdings.sql      # Sample portfolio holdings
│   └── fetch_data.py            # Python script to download price data
├── queries/
│   ├── 01_daily_returns.sql
│   ├── 02_moving_average.sql
│   ├── 03_volatility_ranking.sql
│   ├── 04_portfolio_pnl.sql
│   ├── 05_ytd_by_sector.sql
│   └── 06_best_worst_stocks.sql
├── advanced/
│   ├── create_view.sql
│   ├── add_indexes.sql
│   └── stored_procedure.sql
└── docs/
    └── explain_before_after.png  # Query optimization screenshot
```

---

## 🏗️ Schema design

<!-- Replace this with your ERD screenshot from MySQL Workbench -->
<!-- Database → Reverse Engineer → screenshot the diagram -->

> **ERD diagram**
> <img width="1113" height="786" alt="image" src="https://github.com/user-attachments/assets/050873ed-53af-4663-803c-6cb4eda4497c" />
This ERD represents a Stock Portfolio Management System.

It has 4 tables:
1. stocks

Stores company stock details.

| Column         | Meaning       |
| -------------- | ------------- |
| `stock_id`     | Stock ID      |
| `symbol`       | Stock symbol  |
| `company_name` | Company name  |
| `sector`       | Industry type |

2. portfolio

Stores investor details.
| Column         | Meaning       |
| -------------- | ------------- |
| `portfolio_id` | Portfolio ID  |
| `owner_name`   | Investor name |
| `created_at`   | Created date  |

3. holdings

Stores which stocks are owned in a portfolio.
| Column         | Meaning            |
| -------------- | ------------------ |
| `holding_id`   | Holding ID         |
| `portfolio_id` | Links to portfolio |
| `stock_id`     | Links to stock     |
| `shares`       | Number of shares   |
| `buy_price`    | Purchase price     |

4. daily_prices

Stores daily stock prices.
| Column        | Meaning         |
| ------------- | --------------- |
| `price_id`    | Price record ID |
| `stock_id`    | Related stock   |
| `open_price`  | Opening price   |
| `close_price` | Closing price   |

### Tables

| Table | Description |
|---|---|
| `stocks` | Master list of stock symbols, company names, and sectors |
| `daily_prices` | Daily open, close, and volume for each stock |
| `portfolio` | Portfolio metadata (owner, creation date) |
| `holdings` | Individual stock positions — shares, buy price, buy date |

### Relationships
- `daily_prices.stock_id` → `stocks.stock_id`
- `holdings.stock_id` → `stocks.stock_id`
- `holdings.portfolio_id` → `portfolio.portfolio_id`

---

## ❓ Business questions answered

| # | Question | SQL concepts used |
|---|---|---|
| 1 | What is the daily return % for each stock? | `LAG()`, window functions |
| 2 | What is the 30-day moving average price? | `AVG() OVER`, `ROWS BETWEEN` |
| 3 | Which stock is most volatile? | `STDDEV()`, `RANK()`, CTE |
| 4 | What is my portfolio's current P&L? | Subquery, multi-JOIN |
| 5 | Which sector performed best YTD? | `GROUP BY`, correlated subquery |
| 6 | Which stocks are in the top/bottom quartile? | `NTILE()`, CTE |

---

## 🔍 Key SQL techniques

- **Window functions** — `LAG`, `LEAD`, `RANK`, `NTILE`, `STDDEV` with `PARTITION BY`
- **Rolling windows** — `ROWS BETWEEN 29 PRECEDING AND CURRENT ROW`
- **CTEs** — multi-step logic without nested subqueries
- **Multi-table JOINs** — linking 3–4 tables in a single query
- **Correlated subqueries** — dynamic date filtering per stock
- **Views** — `portfolio_summary` reusable view
- **Stored procedures** — automated P&L calculator
- **Index optimization** — composite index on `(stock_id, price_date)` with `EXPLAIN` before/after

---

## 📊 Key findings

- **TSLA** showed ~3x higher daily return volatility compared to **JPM** in 2023
- **NVDA** delivered the highest YTD return in the portfolio
- **Technology** sector outperformed all other sectors in the dataset
- Adding a composite index on `daily_prices (stock_id, price_date)` reduced query execution time significantly

---

## ▶️ How to run this project

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/sql-stock-portfolio-analysis.git
```

**2. Set up the database in MySQL Workbench**
```sql
CREATE DATABASE stock_portfolio;
USE stock_portfolio;
```

**3. Create tables**
```bash
Run schema/create_tables.sql in MySQL Workbench
```

**4. Download stock data**
```bash
pip install yfinance pandas
python data/fetch_data.py
```

**5. Import CSVs**
```
MySQL Workbench → Right-click daily_prices → Table Data Import Wizard
Import each stock CSV (stock_id column must be included in CSV)
```

**6. Load holdings**
```bash
Run data/sample_holdings.sql in MySQL Workbench
```

**7. Run queries**
```bash
Open any file in queries/ and execute in MySQL Workbench
```

---

## Stored Procedure Screenshot
<img width="627" height="356" alt="image" src="https://github.com/user-attachments/assets/a17e5788-f555-4553-901e-6c067457700e" />


## 💡 Lessons learned

- MySQL's `YEAR(CURDATE())` in subqueries can return empty results if your data doesn't cover the current year — always verify date ranges first with `SELECT DISTINCT YEAR(price_date) FROM daily_prices`
- The Table Data Import Wizard requires `stock_id` to be present in the CSV — solved by adding it during the Python data fetch step
- `EXPLAIN ANALYZE` is invaluable for understanding query performance before and after adding indexes

---

## 📬 Connect

- **LinkedIn:** https://www.linkedin.com/in/gopinath-mdu/
- **Gmail:** vishwagopi23@gmail.com
---

*Built as part of a data analytics portfolio to demonstrate SQL proficiency for data analyst roles.*
