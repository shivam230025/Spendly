"""
Tests for Spec 09 - Delete Expense
(.claude/specs/09-delete-expense.md)
"""
from urllib.parse import urlparse

import pytest
from flask import url_for

from conftest import login, insert_expense
import database.db as db


# --------------------------------------------------------------------- #
# Helpers                                                                #
# --------------------------------------------------------------------- #

def delete_url(app, expense_id):
    with app.test_request_context():
        return url_for("delete_expense", id=expense_id)


def profile_url(app):
    with app.test_request_context():
        return url_for("profile")


def login_url_path(app):
    with app.test_request_context():
        return urlparse(url_for("login")).path


def expense_exists(expense_id):
    return db.get_expense_by_id(expense_id) is not None


@pytest.fixture
def second_user(app):
    """A second user, distinct from the seeded demo user, to test ownership."""
    user_id = db.create_user("Other User", "other@spendly.com", "other123")
    return user_id, {"email": "other@spendly.com", "password": "other123"}


# --------------------------------------------------------------------- #
# Method / auth / ownership guards                                      #
# --------------------------------------------------------------------- #

def test_get_delete_expense_returns_405(client, app, demo_user):
    login(client, app, **demo_user)
    user = db.get_user_by_email(demo_user["email"])
    expense_id = insert_expense(user["id"], 10.0, "Food", "2026-08-01", "Snacks")

    resp = client.get(delete_url(app, expense_id))

    assert resp.status_code == 405
    assert expense_exists(expense_id)


def test_delete_expense_logged_out_redirects_to_login(client, app, demo_user):
    user = db.get_user_by_email(demo_user["email"])
    expense_id = insert_expense(user["id"], 10.0, "Food", "2026-08-01", "Snacks")

    resp = client.post(delete_url(app, expense_id))

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == login_url_path(app)
    assert expense_exists(expense_id)


def test_delete_nonexistent_expense_returns_404(client, app, demo_user):
    login(client, app, **demo_user)

    resp = client.post(delete_url(app, 999999))

    assert resp.status_code == 404


def test_delete_expense_owned_by_other_user_returns_404(client, app, demo_user, second_user):
    other_user_id, _ = second_user
    expense_id = insert_expense(other_user_id, 10.0, "Food", "2026-08-01", "Not yours")

    login(client, app, **demo_user)
    resp = client.post(delete_url(app, expense_id))

    assert resp.status_code == 404
    assert expense_exists(expense_id)


# --------------------------------------------------------------------- #
# Successful deletion                                                   #
# --------------------------------------------------------------------- #

def test_delete_own_expense_succeeds_and_redirects(client, app, demo_user):
    login(client, app, **demo_user)
    user = db.get_user_by_email(demo_user["email"])
    expense_id = insert_expense(user["id"], 10.0, "Food", "2026-08-01", "Snacks")

    resp = client.post(delete_url(app, expense_id))

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == profile_url(app)
    assert not expense_exists(expense_id)


def test_delete_expense_shows_danger_toast_on_profile(client, app, demo_user):
    login(client, app, **demo_user)
    user = db.get_user_by_email(demo_user["email"])
    expense_id = insert_expense(user["id"], 10.0, "Food", "2026-08-01", "Snacks")

    client.post(delete_url(app, expense_id))
    html = client.get(profile_url(app)).get_data(as_text=True)

    assert "toast-danger" in html
    assert "Expense deleted successfully." in html


def test_delete_expense_removes_row_from_profile_table(client, app, demo_user):
    login(client, app, **demo_user)
    user = db.get_user_by_email(demo_user["email"])
    expense_id = insert_expense(user["id"], 10.0, "Food", "2026-08-01", "Unique Snack Description")

    before_html = client.get(profile_url(app)).get_data(as_text=True)
    assert "Unique Snack Description" in before_html

    client.post(delete_url(app, expense_id))
    after_html = client.get(profile_url(app)).get_data(as_text=True)

    assert "Unique Snack Description" not in after_html


def test_delete_expense_updates_stats_and_category_breakdown(client, app, demo_user):
    login(client, app, **demo_user)
    user = db.get_user_by_email(demo_user["email"])
    expense_id = insert_expense(user["id"], 100.0, "Shopping", "2026-08-01", "Big purchase")

    before_html = client.get(profile_url(app)).get_data(as_text=True)
    assert "Shopping" in before_html

    client.post(delete_url(app, expense_id))
    after_html = client.get(profile_url(app)).get_data(as_text=True)

    assert "Big purchase" not in after_html


def test_profile_page_has_delete_column_and_button_for_single_transaction(client, app, demo_user):
    user_id = db.create_user("Solo User", "solo@spendly.com", "solo123")
    insert_expense(user_id, 10.0, "Food", "2026-08-01", "Only expense")
    login(client, app, email="solo@spendly.com", password="solo123")

    html = client.get(profile_url(app)).get_data(as_text=True)

    assert "<th>Delete</th>" in html
    assert "btn-danger" in html
    assert "delete-expense-form" in html
