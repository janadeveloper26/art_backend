# ART Backend

Production-ready Django Ninja backend structure.

## Structure

- `config/`: Core settings and URL configuration.
- `apps/`: Feature-based Django apps.
- `api/`: Django Ninja routers (v1, v2, etc.).
- `core/`: Shared utilities, exceptions, and base classes.

## Getting Started

1. Install UV: `pip install uv`
2. Sync dependencies: `uv sync`
3. Run migrations: `python manage.py migrate`
4. Start dev server: `python manage.py runserver`

## Local HTTPS development

If you need HTTPS locally without native OpenSSL installed, install the required packages and use the helper script from the repo root:

```bash
pip install -r requirements.txt
python backend/scripts/run_https_dev.py --host 127.0.0.1 --port 8000
```

This generates a self-signed certificate for `localhost` and starts Django with `runserver_plus`.
