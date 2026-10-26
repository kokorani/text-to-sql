TextToSQL

Ask questions about your MySQL database in plain English. TextToSQL turns natural language
questions into read-only SQL, runs it against your database, and shows you the results with zero risk of accidentally modifying your data.

Built with [Streamlit](https://streamlit.io/) + [OpenAI](https://platform.openai.com/).

## Features

- **Ask questions in plain English** — "top 5 states by sales" gets turned into SQL and run
  for you.
- **Schema selector** — pick which database and table to analyze from live dropdowns, sourced
  directly from `information_schema` (no hardcoded schemas).
- **Read-only by design** — every generated query is validated before it touches the database.
  `INSERT`, `UPDATE`, `DELETE`, `DROP`, and other mutating statements are rejected outright,
  even if they're hidden inside a subquery, a CTE, or stacked after a semicolon.
- **Email reports** — send a query's results (as a CSV attachment) straight from the app.
- **Schema allow-listing** — optionally restrict which databases show up in the picker, so
  unrelated databases on the same MySQL server never appear.

## How it works

1. You pick a **database** and **table** from the dropdowns.
2. You type a question (e.g. *"Give me the top 5 rows"*).
3. The app sends your question + the table's schema to an LLM, which generates a SQL query.
4. Before running it, the query is validated to make sure it's a single, read-only
   `SELECT` (or `WITH ... SELECT`) statement — anything else is blocked with a clear message.
5. Results are displayed in a table, and can optionally be emailed as a CSV.

## Project structure

| File | Purpose |
|---|---|
| `data_gpt_app.py` | The Streamlit app — UI, schema/table selection, question flow, email report form. |
| `mydb.py` | Database access layer — connection, schema/table discovery, and the read-only query validator (`validate_readonly_query`). |
| `mailer.py` | Sends emailed reports via SMTP. |
| `main.py` | A simple CLI version of the same question → SQL → results loop. |
| `req.txt` | Python dependencies. |

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd <your-repo-name>
python -m venv myenv
source myenv/bin/activate        # on Windows: myenv\Scripts\activate
python -m pip install -r req.txt
```

> **Tip:** Always install with `python -m pip install ...` rather than a bare `pip install ...`
> to make sure packages land in the same environment your `python` is actually using.

### 2. Configure environment variables

Copy the example file and fill in your own values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key, used to generate SQL from questions. |
| `ALLOWED_SCHEMAS` | No | Comma-separated list of databases to show in the schema dropdown (e.g. `analytics,reporting`). If unset, every non-system database your DB user can see is shown. |
| `SMTP_HOST` | For email | SMTP server address (default: `smtp.gmail.com`). |
| `SMTP_PORT` | For email | SMTP port (default: `587`, for TLS). |
| `SMTP_USERNAME` | For email | The email account you're sending from. |
| `SMTP_PASSWORD` | For email | An **app password** for that account — not your regular login password. For Gmail, generate one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2-Step Verification to be enabled first). |
| `SMTP_FROM` | For email | The "From" address shown on sent emails (usually the same as `SMTP_USERNAME`). |

### 3. Configure the database connection

Update the connection string in `mydb.py`:

```python
engine = create_engine(
    "mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
)
```

> **Security note:** for production use, point this at a MySQL user with **read-only
> (`SELECT`-only) grants**, rather than a superuser like `root`. The app already blocks
> mutating queries at the application layer, but a read-only DB user is a stronger,
> defense-in-depth guarantee.

### 4. Run the app

```bash
streamlit run data_gpt_app.py
```

Or, for the CLI version:

```bash
python main.py
```

## Read-only enforcement

Every query goes through `validate_readonly_query()` in `mydb.py` before it's executed. The
validator:

- Parses the SQL and rejects anything that isn't exactly **one** statement (blocking
  `SELECT ...; DROP TABLE ...`-style stacking).
- Confirms the statement actually starts with `SELECT` or `WITH`.
- Scans every token in the statement for forbidden keywords (`INSERT`, `UPDATE`, `DELETE`,
  `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, and others), catching mutations hidden
  inside subqueries or CTEs.

If a query fails validation, `NotAllowedQueryError` is raised and the app shows a clear
"🚫 Not allowed" message instead of running anything against the database.

## Roadmap / ideas

- [ ] DB-level read-only enforcement (dedicated MySQL user with `SELECT`-only grants)
- [ ] Query history / saved queries
- [ ] Support for additional databases (Postgres, etc.)
- [ ] Charting of results, not just tables

## License

Add your license here.
