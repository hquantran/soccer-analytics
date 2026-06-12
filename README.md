# Soccer Analytics

A data pipeline for pulling football (soccer) data from the
[API-SPORTS / API-Football](https://www.api-football.com/) REST API and loading
it into a local [DuckDB](https://duckdb.org/) warehouse using
[dlt](https://dlthub.com/) for downstream analysis.

## Tech stack

- **Python** 3.11+
- **[dlt](https://dlthub.com/)** — extract & load framework (handles schema
  inference, nested JSON flattening, and incremental loads)
- **[DuckDB](https://duckdb.org/)** — local analytical database / warehouse
- **[requests](https://requests.readthedocs.io/)** — HTTP client for the API

## Prerequisites

- Python 3.11 or newer
- An API-SPORTS account and API key — sign up at
  <https://dashboard.api-football.com/>. The free plan is enough to get started
  (see [API plan limits](#api-plan-limits) below).

## Getting started

### 1. Clone the repo

```sh
git clone <your-repo-url>
cd soccer_analytics
```

### 2. Create and activate a virtual environment

```sh
# Create the venv (one time)
python3 -m venv .venv

# Activate it (do this every new shell session)
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell)
```

You'll know it's active when your prompt is prefixed with `(.venv)`. To leave it,
run `deactivate`.

### 3. Install dependencies

```sh
pip install -r requirements.txt
```

### 4. Configure your API key

The real config file (`config.toml`) is **gitignored** so secrets never get
committed. Copy the example and fill in your key:

```sh
cp config.example.toml config.toml
```

Then edit `config.toml` and replace `YOUR_API_KEY_HERE` with your real key:

```toml
[api_sports]
key = "your_real_api_key"
base_url = "https://v3.football.api-sports.io"
```

## API plan limits

If you're on the **free** API-SPORTS plan, keep these constraints in mind — they
shape how the pipeline must be designed:

| Limit | Value |
| --- | --- |
| Requests per day | 100 |
| Requests per minute | ~10 |
| Seasons available | 2022–2024 only |
| Max `page` parameter | 3 (i.e. 60 rows max per paginated query) |

Because of the daily quota, large backfills should be **checkpointed and
resumable**, and routine updates should fetch only what changed (e.g. fixtures
by date window, then refresh stats only for teams that played).

## macOS SSL note

On macOS, the python.org Python build ships without trusting a CA bundle, which
causes `SSL: CERTIFICATE_VERIFY_FAILED` errors for both `pip` and API calls. Fix
it once by running the bundled installer:

```sh
/Applications/Python\ 3.11/Install\ Certificates.command
```

Alternatively, point tools at the `certifi` bundle for a single session:

```sh
export SSL_CERT_FILE="$(python3 -m certifi)"
```

## Project structure

```
soccer_analytics/
├── config.example.toml   # Template config (committed) — copy to config.toml
├── config.toml           # Your real config with API key (gitignored)
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md
```

> Pipeline scripts will be added here as the project develops. The DuckDB file
> (`*.duckdb`) is generated locally and is gitignored.

## Contributing

This is a collaborative project. A few conventions:

- **Never commit secrets.** `config.toml` and `*.duckdb` are gitignored — keep
  it that way. Only `config.example.toml` (with placeholder values) is tracked.
- Always work inside the virtual environment (`source .venv/bin/activate`).
- If you add a dependency, install it and add it to `requirements.txt`.
- Use feature branches and open a pull request for review.
