# Spec: Date Filter for Profile Page

## Overview
Step 05 wired the `/profile` page to real SQLite data, but the transaction history always shows a user's entire expense history with no way to narrow it down. This step adds a date-range filter to the profile page with three presets — **Last 1 Month**, **Last 3 Months**, and **Custom Range** — plus an implicit **All Time** default. Selecting a preset resubmits the page via a GET form, and the transaction table, stats, and category breakdown are recomputed for only the expenses that fall inside the resulting range. With no filter applied, behavior is unchanged from Step 05.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db()`)
- Step 03 — Login + Logout (`session["user_id"]` set on login)
- Step 05 — Backend routes for profile page (`/profile` already sources `user`, `stats`, `transactions`, `category_breakdown` from the database via `get_expenses_by_user`, `get_expense_stats`, `get_category_breakdown`)

## Routes
No new routes. `GET /profile` (already implemented in `app.py`) is extended to read query string parameters:
- `GET /profile?range=1m` — Last 1 Month: expenses from `(today - 30 days)` through `today`, inclusive.
- `GET /profile?range=3m` — Last 3 Months: expenses from `(today - 90 days)` through `today`, inclusive.
- `GET /profile?range=custom&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` — Custom Range: expenses with `date` between `start_date` and `end_date`, inclusive. Both must be present and valid or the filter is ignored (see rules).
- `GET /profile` (no `range`, or an unrecognized `range` value) — All Time: identical to Step 05 behavior, no filtering.

"Last 1 Month" and "Last 3 Months" use a fixed day-count approximation (30 / 90 days) rather than calendar-month arithmetic, to avoid needing a new dependency — this is an intentional simplification for this stage of the project. Access level unchanged: logged-in only (redirect to `/login` if `session.get("user_id")` is absent).

## Database changes
No schema changes. The existing `expenses.date` column (stored as `YYYY-MM-DD` text, per `seed_db()`) is sufficient for range comparison since ISO date strings sort lexicographically.

Modify `database/db.py`:
- `get_expenses_by_user(user_id, start_date=None, end_date=None)` — extend the existing function with optional keyword args. When a bound is provided, append `AND date >= ?` / `AND date <= ?` to the existing parameterised query. When both are `None`, behavior is identical to today (no other callers pass these args, so this is backward compatible).

`get_expense_stats` and `get_category_breakdown` already operate on whatever row list they're given — no changes needed there; `app.py` just needs to pass them the filtered rows instead of the full set.

## Templates
- **Modify:** `templates/profile.html` — add a date-range filter form above the "Transaction History" table:
  - A `<select name="range">` with options `All Time` (value `""`), `Last 1 Month` (value `1m`), `Last 3 Months` (value `3m`), `Custom Range` (value `custom`) — `selected` set to match `filters.range` so the active preset redisplays after submit.
  - Two `<input type="date">` fields (`name="start_date"`, `name="end_date"`), only relevant when `range=custom`; pre-filled with `value="{{ filters.start_date }}"` / `value="{{ filters.end_date }}"`.
  - A small script in `static/js/main.js` shows/enables the two date inputs only when `Custom Range` is selected (and disables/hides them otherwise) so the form stays usable without JS but is clearer with it — this must be a progressive enhancement, not a functional requirement (submitting `range=custom` with the date fields always works server-side regardless of their visibility).
  - A submit button ("Filter") and a "Clear" link back to plain `/profile`.
  - `method="get"` `action="{{ url_for('profile') }}"` so the filter is shareable/bookmarkable and reuses the existing route.
  - If the filtered result set is empty, show a "No transactions in this range" message in place of the table body (reuse the existing empty-state pattern if one exists, otherwise a simple `<tr><td colspan="4">` message).

## Files to change
- `app.py` — `profile()` view: read `range` (and `start_date`/`end_date` when `range=custom`) from `request.args`; resolve them into a concrete `(start_date, end_date)` pair (or `(None, None)` for All Time) per the rules below; pass the resolved bounds to `get_expenses_by_user`; pass a `filters` dict (`{"range": ..., "start_date": ..., "end_date": ...}`) to the template so the form can redisplay the active selection.
- `database/db.py` — extend `get_expenses_by_user` with optional `start_date`/`end_date` keyword arguments as described above. This function only needs concrete `YYYY-MM-DD` bounds — it does not know about presets.
- `templates/profile.html` — add the filter form and empty-state message described above.
- `static/js/main.js` — add the show/hide behavior for the custom date inputs described above.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting/f-strings to build SQL, including for the new date bounds
- Passwords hashed with werkzeug (unchanged in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Resolve `range` in `app.py` before querying: `1m` → `start_date = today - timedelta(days=30)`, `end_date = today`; `3m` → `start_date = today - timedelta(days=90)`, `end_date = today`; `custom` → use `start_date`/`end_date` from `request.args`, validated against `YYYY-MM-DD` (e.g. via `datetime.strptime`); anything else (missing, empty, or unrecognized `range`) → All Time, no bounds
- For `range=custom`, if either date is missing/malformed, or `start_date` is after `end_date`, ignore the filter, flash a message, and fall back to showing all transactions (`range` treated as All Time) — never let a malformed or contradictory range raise an unhandled exception
- `get_expenses_by_user` must keep scoping every query with `WHERE user_id = ?` — a user must never be able to see another user's expenses regardless of what date range is supplied
- Stats and category breakdown must be computed from the same filtered row set as the transaction table — no mismatch between what the table shows and what the stat cards/breakdown bars show
- If a user has zero expenses in the selected range, `/profile` must still render without error (empty table, zero-value stats, empty category breakdown)

## Definition of done
- [ ] Visiting `/profile` without being logged in still redirects to `/login`
- [ ] Visiting `/profile` with no query params (All Time) shows the full transaction history, identical to Step 05 behavior
- [ ] Visiting `/profile?range=1m` as the seeded demo user shows only expenses dated within the last 30 days of today
- [ ] Visiting `/profile?range=3m` as the seeded demo user shows only expenses dated within the last 90 days of today
- [ ] Visiting `/profile?range=custom&start_date=2026-08-01&end_date=2026-08-05` shows only the seeded expenses dated between 2026-08-01 and 2026-08-05 inclusive
- [ ] The stat cards (`Total Spent`, `Transactions`, `Top Category`) on a filtered view (any preset) reflect only the filtered rows, not the full history
- [ ] The category breakdown bars and percentages on a filtered view reflect only the filtered rows and still sum to approximately 100%
- [ ] The `<select>` and, for Custom Range, the date inputs, show the currently active selection after submitting
- [ ] Submitting `range=custom` with `start_date` after `end_date` (an invalid range) does not crash the page — it flashes a message and falls back to showing all transactions
- [ ] Submitting `range=custom` with a malformed or missing date value does not crash the page
- [ ] Filtering to a range with zero matching expenses renders the page with an empty-state message instead of an error
- [ ] Clicking "Clear" returns to `/profile` with the full, unfiltered transaction history (`range` reset to All Time)
