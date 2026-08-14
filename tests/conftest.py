"""
Shared pytest fixtures for the Spendly test suite.

Each test gets a fresh, isolated SQLite file (never the real
`expense_tracker.db`) so tests don't interfere with each other or with
developer data. We reuse the app's own `database/db.py` functions
(`init_db`, `seed_db`, `get_db`, `create_user`) rather than hand-writing
schema SQL here.
"""
import os
import tempfile

import pytest

import database.db as db

# `app.py` runs `init_db()` / `seed_db()` at import time (inside
# `with app.app_context(): ...`). Point DB_PATH at a throwaway file
# *before* importing app.py for the first time, so that first-import
# side effect never touches the real project database.
_bootstrap_fd, _bootstrap_path = tempfile.mkstemp(suffix=".db")
os.close(_bootstrap_fd)
db.DB_PATH = _bootstrap_path

import app as app_module  # noqa: E402  (import after DB_PATH patch, intentional)


@pytest.fixture
def app():
    """Flask app configured for testing, backed by a fresh temp SQLite file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.DB_PATH = path

    db.init_db()
    db.seed_db()

    app_module.app.config.update(TESTING=True)

    yield app_module.app

    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def demo_user():
    """Credentials for the user inserted by seed_db()."""
    return {"email": "demo@spendly.com", "password": "demo123"}


def login(client, app, email, password):
    """Log the test client in as the given user via the real /login route."""
    with app.test_request_context():
        from flask import url_for

        url = url_for("login")
    return client.post(url, data={"email": email, "password": password}, follow_redirects=False)


def insert_expense(user_id, amount, category, date_str, description):
    """Insert one expense row directly via the app's own get_db() connection.

    Not a call to a nonexistent "add_expense" helper in db.py -- there is
    none -- but it reuses get_db() rather than hand-rolling a new sqlite
    connection/schema, matching the same table db.py itself defines.
    """
    conn = db.get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date_str, description),
        )
        conn.commit()
    finally:
        conn.close()
