# Spec: Edit Expense

## Overview
`GET /expenses/<id>/edit` currently returns the placeholder string `"Edit expense — coming in Step 8"`. This step replaces it with a real form that lets a logged-in user update an existing expense they own. It follows directly from Step 7 (add expense): where add-expense inserts a new row, edit-expense pre-fills the same form fields from an existing row and updates it in place, continuing Spendly's expense-management flow (add/edit/delete). This step also adds the entry point to that form: an "Edit" column at the right of the Transaction History table on `/profile`, with an edit button on every row.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db()`)
- Step 02 — Registration (users exist to own expenses)
- Step 03 — Login + Logout (`session["user_id"]` identifies the owner)
- Step 05 — Backend routes for profile page (`/profile` renders `transactions` from real `expenses` rows — edited rows must show up there)
- Step 07 — Add expense (`VALID_CATEGORIES`, `create_expense()` pattern, `add_expense.html` form markup this step mirrors)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the expense's current values — logged-in only, owner only
- `POST /expenses/<int:id>/edit` — validate and update the expense, then redirect to `/profile` — logged-in only, owner only

Both are the same `/expenses/<id>/edit` route handling both methods (matches the existing `add_expense` pattern of one view function keyed on `request.method`).

## Database changes
No schema changes. The existing `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) already has every column this form needs.

New query helpers to add to `database/db.py`:
- `get_expense_by_id(expense_id)` — `SELECT * FROM expenses WHERE id = ?`, parameterised, mirrors the `try/finally: conn.close()` pattern used by `get_user_by_id()`. Returns `None` if no row matches.
- `update_expense(expense_id, amount, category, date, description)` — `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?`, parameterised, same `try/finally: conn.close()` pattern as `create_expense()`

## Templates
- **Create:** `templates/edit_expense.html` — the edit-expense form, extends `base.html`, structurally identical to `add_expense.html` but pre-filled with the existing row's values and posting to `/expenses/<id>/edit`
- **Modify:** `templates/profile.html` — add an "Edit" column at the right of the `profile-table-amount-col` column in the Transaction History table. Add a `<th>Edit</th>` header and, in every row, a `<td>` containing a link/button to `{{ url_for('edit_expense', id=tx.id) }}`, styled like the existing "+ Add Expense" button (`.btn-primary`). Update the empty-state row's `colspan` from `4` to `5`.

## Files to change
- `app.py` — replace the placeholder `edit_expense(id)` view with a real `GET`/`POST` implementation: auth guard, ownership check, form pre-fill, validation, calling `update_expense()`, flashing errors, redirecting to `/profile` on success. Also update the `profile()` view's `transactions` list comprehension to include `"id": row["id"]` so each row can link to its edit page.
- `database/db.py` — add `get_expense_by_id()` and `update_expense()`
- `templates/profile.html` — add the Edit column described above
- `static/css/style.css` — if the existing `.btn-primary` button is visually too large for a table cell, add a small size-only modifier (e.g. `.btn-primary.btn-sm`) that adjusts padding/font-size via existing CSS variables; do not introduce a new color or a duplicate button style

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting/f-strings to build SQL
- Passwords hashed with werkzeug (n/a to this step, no auth changes)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route requires `session.get("user_id")`; unauthenticated requests redirect to `/login` (mirror the guard already used in `profile()` / `add_expense()`)
- Look up the expense with `get_expense_by_id(id)`. If it does not exist, `abort(404)`.
- Ownership check: if the expense's `user_id` does not match `session["user_id"]`, `abort(404)` (not 403 — do not reveal that a row exists for another user)
- Never take `user_id` from form input; the expense stays owned by its original `user_id` — only `amount`, `category`, `date`, and `description` are updatable
- Validate on the server (not just client-side `required` attributes), same rules as `add_expense`:
  - `amount` must parse as a positive number
  - `category` must be one of `VALID_CATEGORIES` (Food, Transport, Bills, Health, Entertainment, Shopping, Other), rendered as a `<select>` so `category_breakdown`'s `bar-<category|lower>` CSS classes keep applying
  - `date` must parse as a valid `YYYY-MM-DD` date
  - `description` is optional
- On `GET`, pre-fill the form's `values` dict from the fetched row (not from `request.form`)
- On validation failure (`POST`): flash a specific error message and re-render `edit_expense.html` with the submitted values preserved (mirror the `add_expense()` re-render-with-flash pattern), do not write a partial update
- On success: flash `"Expense updated successfully."` with the `"success"` category (mirrors `add_expense()`'s `flash("Expense added successfully.", "success")`, which `profile.html` already renders via its `toast toast-success` block), then redirect to `/profile` (`url_for("profile")`) so the updated expense shows up in the transaction history immediately
- Close every `sqlite3` connection opened in `get_expense_by_id()` and `update_expense()` (`try/finally: conn.close()`)
- Reuse existing `.form-group` / `.form-input` / `.btn-submit` CSS classes from `style.css` for the form — do not introduce new form styling
- The Edit column's per-row button must reuse `.btn-primary` (same class as the existing "+ Add Expense" button) so it matches that button's color, border-radius, and hover state; only a size adjustment is allowed if needed for the table cell, via CSS variables already defined in `style.css`
- The Edit column header and per-row button must appear for every transaction row, including when a user has only one transaction; the empty-state row (no transactions in range) does not get an edit button

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` without being logged in redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an `id` that doesn't exist returns HTTP 404
- [ ] Logging in as one user and visiting `/expenses/<id>/edit` for an expense owned by a different user returns HTTP 404
- [ ] Logging in as the seeded demo user and visiting `/expenses/<id>/edit` for one of their own expenses returns HTTP 200 with the form pre-filled with that expense's current amount, category, date, and description
- [ ] Submitting the form with valid changes redirects to `/profile` and the transaction history reflects the updated values (not a duplicate row)
- [ ] After a successful edit, `/profile` displays a "Expense updated successfully." success toast, matching how "Expense added successfully." appears after adding an expense
- [ ] Submitting a negative or non-numeric amount re-renders the form with an error and does not modify the row
- [ ] Submitting an invalid or missing date re-renders the form with an error and does not modify the row
- [ ] Submitting with `description` cleared succeeds (description is optional)
- [ ] After editing an expense, `/profile`'s `stats.total_spent`, `stats.transaction_count`, and `category_breakdown` reflect the updated value without a server restart
- [ ] `/profile`'s Transaction History table shows an "Edit" column to the right of "Amount", with an edit button in every transaction row
- [ ] Clicking a row's edit button navigates to `/expenses/<id>/edit` for that exact row's expense
- [ ] The edit button's visual style (color, shape, hover) matches the existing "+ Add Expense" button
