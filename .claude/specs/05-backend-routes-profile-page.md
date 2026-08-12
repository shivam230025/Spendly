# Spec: Backend Routes for Profile Page

## Overview
Step 04 built the `/profile` page against hardcoded Python dicts and lists so the UI could be validated in isolation. This step replaces that hardcoded data with real SQLite queries: the logged-in user's actual name/email/member-since, their real transaction history, and stats/category-breakdown values computed from their `expenses` rows. The route, template, and auth guard already exist — this step only changes where the data comes from.

## Depends on
- Step 01 — Database setup (`users`, `expenses` tables; `get_db()`)
- Step 02 — Registration (real users exist to query)
- Step 03 — Login + Logout (`session["user_id"]` is set on login)
- Step 04 — Profile page design (`templates/profile.html` already renders `user`, `stats`, `transactions`, `category_breakdown` — this step keeps that same shape)

## Routes
No new routes. `GET /profile` (already implemented in `app.py`) is modified in place to source its context from the database instead of hardcoded values. Access level unchanged: logged-in only (redirect to `/login` if `session.get("user_id")` is absent).

## Database changes
No schema changes. The existing `users` and `expenses` tables (see `database/db.py`) hold everything needed.

New query helper functions to add to `database/db.py` (all parameterised, all take `user_id`):
- `get_user_by_id(user_id)` — `SELECT * FROM users WHERE id = ?`, returns the row or `None`
- `get_expenses_by_user(user_id)` — `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC`, returns all rows
- `get_expense_stats(user_id)` — returns total spent, transaction count, and top category for the user (derived from `get_expenses_by_user` results or a dedicated aggregate query)
- `get_category_breakdown(user_id)` — returns per-category totals and each category's percent of total spend, for the same categories shown by the breakdown bars

## Templates
- **Modify:** none required. `templates/profile.html` already consumes `user.initials`, `user.name`, `user.email`, `user.member_since`, `stats.total_spent`, `stats.transaction_count`, `stats.top_category`, `transactions[].{date,description,category,amount}`, and `category_breakdown[].{category,amount,percent,css_class}` — the view must keep producing exactly this shape from real data.
  - `user.initials` and `user.member_since` are not stored columns; derive `initials` from `user.name` and `member_since` from `users.created_at` in the view function.
  - `category_breakdown[].css_class` must keep the `bar-<category|lower>` convention already used by the CSS (e.g. `bar-food`, `bar-bills`) so existing styles keep applying without CSS changes.

## Files to change
- `app.py` — rewrite the `profile()` view to call the new `database/db.py` helpers instead of building hardcoded `user`/`stats`/`transactions`/`category_breakdown` values; keep the existing `session.get("user_id")` auth guard
- `database/db.py` — add `get_user_by_id()`, `get_expenses_by_user()`, `get_expense_stats()`, `get_category_breakdown()`

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting/f-strings to build SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Every new DB helper takes `user_id` as a parameter and scopes its query with `WHERE user_id = ?` — a user must never be able to see another user's expenses
- If a user has zero expenses, `/profile` must still render (empty transaction table, zero-value stats, empty category breakdown) rather than erroring
- Compute `stats.total_spent`, `stats.transaction_count`, `stats.top_category`, and the `category_breakdown` percentages in Python or SQL — do not hardcode any of these values
- Keep the existing auth guard in `profile()`: `if not session.get("user_id"): return redirect(url_for("login"))`
- Close every `sqlite3` connection opened in a new helper (mirror the `try/finally: conn.close()` pattern already used in `create_user()` / `get_user_by_email()`)

## Definition of done
- [ ] Visiting `/profile` without being logged in still redirects to `/login`
- [ ] Logging in as the seeded demo user (`demo@spendly.com` / `demo123`) and visiting `/profile` returns HTTP 200 with their real name/email shown
- [ ] The transaction history table shows the demo user's actual seeded expenses (8 rows), not the old hardcoded 6 rows
- [ ] `stats.total_spent` on the page equals the sum of the demo user's seeded expense amounts
- [ ] `stats.transaction_count` on the page equals the demo user's actual expense row count
- [ ] The category breakdown percentages sum to approximately 100% and match the demo user's actual per-category totals
- [ ] Registering a brand-new user with zero expenses and visiting `/profile` renders without error (empty table, zero stats)
- [ ] No hardcoded `user`, `stats`, `transactions`, or `category_breakdown` values remain in `app.py`'s `profile()` view
