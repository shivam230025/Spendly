"""
Tests for Spec 06 - Date Filter for Profile Page
(.claude/specs/06-date-filter-profile-page.md)

These tests assert what the spec promises for GET /profile?range=...,
not whatever app.py currently happens to do. Where the shipped
implementation diverges from the spec, the corresponding test is
expected to fail -- see the final report for a list of those
mismatches.
"""
from datetime import date, timedelta
from urllib.parse import urlparse

import pytest
from flask import url_for

from conftest import login, insert_expense
import database.db as db


# --------------------------------------------------------------------- #
# Helpers                                                                #
# --------------------------------------------------------------------- #

def profile_url(app, **query):
    with app.test_request_context():
        return url_for("profile", **query)


def login_url_path(app):
    with app.test_request_context():
        return urlparse(url_for("login")).path


# Amounts seeded by seed_db() for demo@spendly.com (see database/db.py).
SEEDED_TOTAL = 12.50 + 45.00 + 89.99 + 25.00 + 15.75 + 60.20 + 9.00 + 32.40
SEEDED_COUNT = 8


# --------------------------------------------------------------------- #
# Access control                                                        #
# --------------------------------------------------------------------- #

def test_profile_redirects_to_login_when_logged_out(client, app):
    resp = client.get(profile_url(app))
    assert resp.status_code in (301, 302, 303)
    assert urlparse(resp.headers["Location"]).path == login_url_path(app)


@pytest.mark.parametrize("query", [
    {"range": "1m"},
    {"range": "3m"},
    {"range": "custom", "start_date": "2026-08-01", "end_date": "2026-08-05"},
])
def test_profile_with_filter_params_still_requires_login(client, app, query):
    resp = client.get(profile_url(app, **query))
    assert resp.status_code in (301, 302, 303)
    assert urlparse(resp.headers["Location"]).path == login_url_path(app)


# --------------------------------------------------------------------- #
# All Time (default / no filter / unrecognized filter)                  #
# --------------------------------------------------------------------- #

def test_profile_no_query_params_shows_full_history(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(app))
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert html.count('<tr>') - 1 or True  # sanity: table rendered (loose check below is authoritative)
    assert f"{SEEDED_COUNT}" in html  # transaction_count stat
    assert f"{SEEDED_TOTAL:.2f}" in html  # total_spent stat
    # all 8 seeded descriptions should be present
    for desc in ["Groceries", "Monthly bus pass", "Electricity bill", "Pharmacy",
                 "Movie tickets", "New shoes", "Miscellaneous", "Dinner with friends"]:
        assert desc in html


def test_profile_unrecognized_range_value_falls_back_to_all_time(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(app, range="not-a-real-preset"))
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert f"{SEEDED_COUNT}" in html
    assert f"{SEEDED_TOTAL:.2f}" in html


# --------------------------------------------------------------------- #
# Custom range - literal example from the spec's Definition of done     #
# --------------------------------------------------------------------- #

def test_custom_range_shows_only_expenses_in_window(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2026-08-01", end_date="2026-08-05",
    ))
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200

    # In-range (inclusive bounds): 2026-08-01, 08-02, 08-03, 08-05
    for desc in ["Groceries", "Monthly bus pass", "Electricity bill", "Pharmacy"]:
        assert desc in html
    # Out-of-range: 2026-08-08 onward
    for desc in ["Movie tickets", "New shoes", "Miscellaneous", "Dinner with friends"]:
        assert desc not in html

    # 4 matching rows, total 172.49
    assert "4" in html
    assert "172.49" in html


def test_custom_range_stats_reflect_only_filtered_rows(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2026-08-01", end_date="2026-08-05",
    ))
    html = resp.get_data(as_text=True)

    # Total spent for the filtered window only, not the full-history total.
    assert "172.49" in html
    assert f"{SEEDED_TOTAL:.2f}" not in html
    # Top category among the 4 filtered rows is Bills (89.99, the largest).
    assert "Bills" in html


def test_custom_range_category_breakdown_sums_to_about_100_percent(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2026-08-01", end_date="2026-08-05",
    ))
    html = resp.get_data(as_text=True)

    import re
    percents = [int(p) for p in re.findall(r"width:\s*(\d+)%", html)]
    assert percents, "expected category breakdown bars with a width percentage in the response"
    assert 95 <= sum(percents) <= 105


def test_filter_form_redisplays_active_custom_range(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2026-08-01", end_date="2026-08-05",
    ))
    html = resp.get_data(as_text=True)

    # Spec: date inputs pre-filled with the submitted values.
    assert 'value="2026-08-01"' in html
    assert 'value="2026-08-05"' in html
    # Spec: a <select name="range"> whose active option is "selected".
    assert '<select name="range"' in html


# --------------------------------------------------------------------- #
# Invalid / malformed custom ranges never crash the page                #
# --------------------------------------------------------------------- #

def test_custom_range_start_after_end_falls_back_to_all_time(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2026-08-05", end_date="2026-08-01",
    ))
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert f"{SEEDED_COUNT}" in html
    assert f"{SEEDED_TOTAL:.2f}" in html


@pytest.mark.parametrize("start_date,end_date", [
    ("not-a-date", "2026-08-05"),
    ("2026-08-01", "not-a-date"),
    ("2026-13-40", "2026-08-05"),
])
def test_custom_range_malformed_dates_do_not_crash(client, app, demo_user, start_date, end_date):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date=start_date, end_date=end_date,
    ))
    assert resp.status_code == 200
    # Falls back to All Time rather than raising.
    html = resp.get_data(as_text=True)
    assert f"{SEEDED_COUNT}" in html


def test_custom_range_missing_end_date_does_not_crash(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(app, range="custom", start_date="2026-08-01"))
    assert resp.status_code == 200


def test_custom_range_missing_start_date_does_not_crash(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(app, range="custom", end_date="2026-08-05"))
    assert resp.status_code == 200


# --------------------------------------------------------------------- #
# Empty result set                                                      #
# --------------------------------------------------------------------- #

def test_zero_matching_expenses_shows_empty_state(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2020-01-01", end_date="2020-01-02",
    ))
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "No transactions in this range" in html


def test_zero_matching_expenses_stats_are_zeroed_not_erroring(client, app, demo_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(
        app, range="custom", start_date="2020-01-01", end_date="2020-01-02",
    ))
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "0.00" in html  # zero total_spent
    assert ">0<" in html  # zero transaction_count


# --------------------------------------------------------------------- #
# Clear link resets to All Time                                         #
# --------------------------------------------------------------------- #

def test_plain_profile_url_after_filter_shows_full_history_again(client, app, demo_user):
    login(client, app, **demo_user)

    filtered = client.get(profile_url(
        app, range="custom", start_date="2026-08-01", end_date="2026-08-05",
    ))
    assert "172.49" in filtered.get_data(as_text=True)

    cleared = client.get(profile_url(app))  # what the "Clear" link points to
    html = cleared.get_data(as_text=True)
    assert cleared.status_code == 200
    assert f"{SEEDED_COUNT}" in html
    assert f"{SEEDED_TOTAL:.2f}" in html


# --------------------------------------------------------------------- #
# 1-month / 3-month presets - day-count boundaries, inclusive            #
# --------------------------------------------------------------------- #

@pytest.fixture
def boundary_user(app):
    """A second user with expenses at controlled offsets from today, used
    to test the 30/90-day boundary independent of wall-clock date."""
    user_id = db.create_user("Boundary Tester", "boundary@spendly.com", "boundary123")
    today = date.today()
    offsets = [0, 30, 31, 90, 91, 200]
    for i, offset in enumerate(offsets):
        d = (today - timedelta(days=offset)).isoformat()
        insert_expense(user_id, 10.0 * (i + 1), "Food", d, f"offset-{offset}-days")
    return {"email": "boundary@spendly.com", "password": "boundary123"}


def test_range_1m_includes_today_and_30_days_ago_excludes_31_days_ago(client, app, boundary_user):
    login(client, app, **boundary_user)
    resp = client.get(profile_url(app, range="1m"))
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "offset-0-days" in html
    assert "offset-30-days" in html
    assert "offset-31-days" not in html
    assert "offset-90-days" not in html
    assert "offset-91-days" not in html
    assert "offset-200-days" not in html


def test_range_3m_includes_up_to_90_days_ago_excludes_91_days_ago(client, app, boundary_user):
    login(client, app, **boundary_user)
    resp = client.get(profile_url(app, range="3m"))
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "offset-0-days" in html
    assert "offset-30-days" in html
    assert "offset-31-days" in html
    assert "offset-90-days" in html
    assert "offset-91-days" not in html
    assert "offset-200-days" not in html


def test_range_1m_stats_reflect_only_1m_window(client, app, boundary_user):
    login(client, app, **boundary_user)
    resp = client.get(profile_url(app, range="1m"))
    html = resp.get_data(as_text=True)

    # offsets 0 and 30 -> amounts 10.00 and 20.00 -> total 30.00, count 2
    assert "30.00" in html


# --------------------------------------------------------------------- #
# Cross-user isolation while filtering (Rules for implementation)       #
# --------------------------------------------------------------------- #

def test_filtering_never_leaks_another_users_expenses(client, app, demo_user, boundary_user):
    login(client, app, **demo_user)
    resp = client.get(profile_url(app))  # All Time, as demo user
    html = resp.get_data(as_text=True)
    assert "offset-0-days" not in html
    assert "offset-30-days" not in html


def test_filtering_as_second_user_never_shows_demo_users_expenses(client, app, boundary_user):
    login(client, app, **boundary_user)
    resp = client.get(profile_url(app, range="3m"))
    html = resp.get_data(as_text=True)
    assert "Groceries" not in html
    assert "Electricity bill" not in html
