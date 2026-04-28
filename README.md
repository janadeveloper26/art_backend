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
