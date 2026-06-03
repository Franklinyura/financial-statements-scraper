# 📊 Financial Statements Web Scraper

Automated pipeline that scrapes financial statements published on the websites of regulated entities and loads the results directly into a relational database.

Built as part of data engineering work in the financial regulatory sector (Dominican Republic).

---

## 🔧 What it does

1. Iterates over a list of regulated entities (banks, insurance companies, etc.)
2. Fetches each entity's public webpage and parses the HTML
3. Extracts links and text that match configurable keyword filters
4. Detects the publication year from URLs and link text using regex
5. Deduplicates results and loads them into a database table via SQLAlchemy

---

## 🗂 Project structure

```
├── scraper.py                   # Main pipeline
├── ef_estados_financieros.py    # Entity config (not included — see below)
├── .env.example                 # Environment variable template
├── requirements.txt
└── README.md
```

> `ef_estados_financieros.py` contains the entity dictionary with URLs and keyword configs. It is excluded from this repo as it contains internal configuration.

---

## ⚙️ Configuration

All credentials and settings are loaded from environment variables. Copy `.env.example` to `.env` and fill in your values — **never commit `.env` to git**.

```env
DB_DIALECT=postgresql+psycopg2 
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_TABLE=estados_financieros

```

---

## 📦 Requirements

```
requests
beautifulsoup4
pandas
sqlalchemy
openpyxl
python-dotenv
# Add your DB driver:
# psycopg2-binary       → PostgreSQL
# oracledb              → Oracle
# pyodbc                → SQL Server
# pymysql               → MySQL
```

---

## 🧠 Tech stack

`Python` · `BeautifulSoup4` · `Pandas` · `SQLAlchemy` · `Requests` · `Regex`

---
