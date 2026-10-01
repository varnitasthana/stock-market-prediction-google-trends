"""Apply migrations, then start the API server.

Used as the container entrypoint so a fresh deployment never serves an empty
database. Alembic is idempotent, so restarting an existing container is a no-op
for the schema. Bootstrap seeding stays opt-in because it calls out to Google
and yfinance; run it explicitly with::

    docker compose exec backend python scripts/bootstrap_demo.py
"""

import os
import subprocess
import sys


def log(message: str) -> None:
    print(f"[entrypoint] {message}", flush=True)


def run_migrations() -> None:
    """Bring the database schema up to head."""
    if os.getenv("SKIP_MIGRATIONS", "").lower() in {"1", "true", "yes"}:
        log("SKIP_MIGRATIONS set; skipping migrations.")
        return

    log("Applying database migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    if result.returncode != 0:
        log(f"Migrations failed with exit code {result.returncode}. Refusing to start.")
        raise SystemExit(result.returncode)
    log("Schema is up to date.")


def serve() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    reload_enabled = os.getenv("RELOAD", "").lower() in {"1", "true", "yes"}

    import uvicorn

    log(f"Starting API on {host}:{port} (reload={reload_enabled})")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=int(port),
        reload=reload_enabled,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


def main() -> None:
    run_migrations()
    serve()


if __name__ == "__main__":
    main()