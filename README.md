# Financial Statements Web Scraper

Automated pipeline that scrapes financial statements published on the websites of regulated entities and loads the results directly into a relational database.

Built as part of data engineering work in the financial regulatory sector (Dominican Republic).

---

## What it does

1. Iterates over a list of regulated entities (banks, insurance companies, etc.)
2. Fetches each entity's public webpage and parses the HTML
3. Extracts links and text that match configurable keyword filters
4. Detects the publication year from URLs and link text using regex
5. Deduplicates results and loads them into a database table via SQLAlchemy

---

## Project structure

```
├── scraper.py                   # Main pipeline
├── ef_estados_financieros.py    # Entity config (not included)
├── requirements.txt
└── README.md
```

## Requirements

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

## Tech stack

`Python` · `BeautifulSoup4` · `Pandas` · `SQLAlchemy` · `Requests` · `Regex`

---
