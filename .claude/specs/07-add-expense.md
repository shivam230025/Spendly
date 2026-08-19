# Spec: Add Expense

## Overview
`GET /expenses/add` currently returns the placeholder string `"Add expense — coming in Step 7"`. This step replaces it with a real form page that lets a logged-in user record a new expense against their account. It is the first step in Spendly's expense-management flow (add/edit/delete) and is what will start populating the `expenses` table from the UI instead of only from `seed_db()`.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db()`)
- Step 02 — Registration (users exist to own expenses)
- Step 03 — Login + Logout (`session["user_id"]` identifies the owner)
- Step 05 — Backend routes for profile page (`/profile` already renders `transactions` from real `expenses` rows — this step is what will start filling that table from user input)

## Routes
- `GET /expenses/add` — render the empty add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the new expense, then redirect to `/profile` — logged-in only

Both are the same `/expenses/add` route handling both methods (matches the existing `register`/`login` pattern of one view function keyed on `request.method`).

## Database changes
No schema changes. The existing `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) already has every column this form needs.

New query helper to add to `database/db.py`:
- `create_expense(user_id, amount, category, date, description)` — `INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)`, parameterised, mirrors the `try/finally: conn.close()` pattern used by `create_user()`

## Templates
- **Create:** `templates/add_expense.html` — the add-expense form, extends `base.html`
- **Modify:** none. `templates/profile.html` already lists `transactions` and needs no changes to display newly-added rows.

## Files to change
- `app.py` — replace the placeholder `add_expense()` view with a real `GET`/`POST` implementation: auth guard, form validation, calling `create_expense()`, flashing errors, redirecting to `/profile` on success
- `database/db.py` — add `create_expense()`

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting/f-strings to build SQL
- Passwords hashed with werkzeug (n/a to this step, no auth changes)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route requires `session.get("user_id")`; unauthenticated requests redirect to `/login` (mirror the guard already used in `profile()`)
- The expense is always inserted with `user_id = session["user_id"]` — never take `user_id` from form input
- Validate on the server (not just client-side `required` attributes):
  - `amount` must parse as a positive number
  - `category` must be one of the fixed set already styled in `style.css`: Food, Transport, Bills, Health, Entertainment, Shopping, Other (render this as a `<select>`, not a free-text field, so `category_breakdown`'s `bar-<category|lower>` CSS classes keep applying)
  - `date` must parse as a valid `YYYY-MM-DD` date
  - `description` is optional
- On validation failure: flash a specific error message and re-render `add_expense.html` with the submitted values preserved (mirror the `register()` re-render-with-flash pattern), do not insert a partial row
- On success: redirect to `/profile` (`url_for("profile")`) so the new expense shows up in the transaction history immediately
- Close every `sqlite3` connection opened in `create_expense()` (`try/finally: conn.close()`)
- Reuse existing `.form-group` / `.form-input` / `.btn-submit` CSS classes from `style.css` for the form — do not introduce new form styling

## Definition of done
- [ ] Visiting `/expenses/add` without being logged in redirects to `/login`
- [ ] Logging in as the seeded demo user and visiting `/expenses/add` returns HTTP 200 with a form (amount, category dropdown, date, description)
- [ ] Submitting the form with valid data redirects to `/profile` and the new expense appears in the transaction history table
- [ ] The new expense's `user_id` in the database matches the logged-in user's id, regardless of what (if anything) was submitted in the form
- [ ] Submitting a negative or non-numeric amount re-renders the form with an error and does not create a row
- [ ] Submitting an invalid or missing date re-renders the form with an error and does not create a row
- [ ] Submitting with `description` left blank succeeds (description is optional)
- [ ] After adding an expense, `/profile`'s `stats.total_spent`, `stats.transaction_count`, and `category_breakdown` reflect the new expense without a server restart
