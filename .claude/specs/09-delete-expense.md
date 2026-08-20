# Spec: Delete Expense

## Overview
`GET /expenses/<id>/delete` currently returns the placeholder string `"Delete expense — coming in Step 9"`. This step replaces it with a real action that lets a logged-in user permanently remove an expense they own, completing Spendly's expense-management flow (add/edit/delete) started in Steps 7 and 8. Because deletion is destructive and irreversible, the route accepts `POST` only (never `GET`, which browsers, crawlers, and prefetchers can trigger unintentionally) and the UI asks for confirmation before submitting.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db()`)
- Step 02 — Registration (users exist to own expenses)
- Step 03 — Login + Logout (`session["user_id"]` identifies the owner)
- Step 05 — Backend routes for profile page (`/profile` renders `transactions` from real `expenses` rows — deleted rows must disappear from there)
- Step 08 — Edit expense (`get_expense_by_id()`, the ownership-check pattern, and the "Edit" column this step adds a "Delete" column beside)

## Routes
- `POST /expenses/<int:id>/delete` — delete the expense, then redirect to `/profile` — logged-in only, owner only

The existing `GET /expenses/<id>/delete` placeholder is removed; `GET` on this path is no longer supported (a `GET` request now returns Flask's default 405, since only `methods=["POST"]` is registered).

## Database changes
No schema changes. The existing `expenses` table already supports row deletion by `id`.

New query helper to add to `database/db.py`:
- `delete_expense(expense_id)` — `DELETE FROM expenses WHERE id = ?`, parameterised, same `try/finally: conn.close()` pattern as `update_expense()`

## Templates
- **Modify:** `templates/profile.html` — add a "Delete" column to the right of the existing "Edit" column in the Transaction History table. Add a `<th>Delete</th>` header and, in every row, a `<td>` containing a `<form method="POST" action="{{ url_for('delete_expense', id=tx.id) }}" class="delete-expense-form">` wrapping a single `<button type="submit" class="btn-danger">Delete</button>`. Update the empty-state row's `colspan` from `5` to `6`. Also add a second `{% with %}` flash block right after the existing `success_messages` block, filtered on `category_filter=["danger"]`, rendering `<div class="toast toast-danger">{{ danger_messages[0] }}</div>` — structurally identical to the `toast-success` block, just a different category/class.
- **Modify:** `templates/base.html` — none expected.

## Files to change
- `app.py` — replace the placeholder `delete_expense(id)` view with a real implementation: change `methods` to `["POST"]` only, auth guard, ownership check via `get_expense_by_id(id)`, call `delete_expense(id)`, `flash("Expense deleted successfully.", "danger")`, redirect to `/profile`
- `database/db.py` — add `delete_expense(expense_id)`
- `templates/profile.html` — add the Delete column and the `toast-danger` flash block described above
- `static/css/style.css` — add two classes using the existing unused `--danger` / `--danger-light` variables (do not introduce new hex values):
  - `.btn-danger` — same sizing/shape rules as `.btn-primary` so the Edit/Delete buttons align in the table row, but `background: var(--danger-light)` / `color: var(--danger)` with a `var(--danger)` border, darkening to `var(--danger)` background on hover (mirrors how `.btn-primary:hover` swaps to `--accent`)
  - `.toast-danger` — same shape/shadow/animation as `.toast-success` (which it sits alongside, sharing the base `.toast` class), but `background: var(--danger-light)`, `color: var(--danger)`, `border: 1px solid var(--danger)` instead of the accent (green) colors — same light-red pairing as `.btn-danger` and the existing `.auth-error` block
- `static/js/main.js` — add a confirmation guard: attach a `submit` listener to every `.delete-expense-form` that calls `window.confirm("Delete this expense? This cannot be undone.")` and calls `event.preventDefault()` if the user cancels

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting/f-strings to build SQL
- Passwords hashed with werkzeug (n/a to this step, no auth changes)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route requires `session.get("user_id")`; unauthenticated requests redirect to `/login` (mirror the guard already used in `edit_expense()`)
- Route accepts `POST` only — no `GET` handler, so the deletion cannot be triggered by a plain link, browser prefetch, or crawler
- Look up the expense with `get_expense_by_id(id)` before deleting. If it does not exist, `abort(404)`.
- Ownership check: if the expense's `user_id` does not match `session["user_id"]`, `abort(404)` (not 403 — do not reveal that a row exists for another user), mirroring `edit_expense()`
- Never delete based on any value from the request body other than the `id` in the URL
- On success: `flash("Expense deleted successfully.", "danger")` — same `flash(message, category)` mechanism `add_expense()`/`edit_expense()` use for their `"success"` toast, just a different category string so it renders in the light-red `toast-danger` style instead of green — then redirect to `/profile`
- Close every `sqlite3` connection opened in `delete_expense()` (`try/finally: conn.close()`)
- The client-side confirmation in `main.js` is a UX safeguard only, not a security control — the server-side auth/ownership checks are what actually protect the data
- The Delete button must use the new `.btn-danger` class (distinct color from `.btn-primary`, built from `--danger`/`--danger-light`) so it is visually distinguishable from Edit and clearly signals a destructive action
- The Delete column header and per-row button must appear for every transaction row, including when a user has only one transaction; the empty-state row (no transactions in range) does not get a delete button

## Definition of done
- [ ] Visiting `/expenses/<id>/delete` with `GET` (e.g. typing the URL directly) returns HTTP 405, not a deletion
- [ ] Submitting the delete form while logged out redirects to `/login` and does not delete the row
- [ ] Submitting the delete form for an `id` that doesn't exist returns HTTP 404
- [ ] Logging in as one user and submitting the delete form for an expense owned by a different user returns HTTP 404 and does not delete the row
- [ ] Logging in as the seeded demo user and submitting the delete form for one of their own expenses removes it and redirects to `/profile`
- [ ] After a successful delete, `/profile` displays an "Expense deleted successfully." toast using the same flash-then-redirect mechanism as "Expense added successfully."/"Expense updated successfully.", but rendered in the light-red `toast-danger` style instead of green
- [ ] After deleting an expense, `/profile`'s `stats.total_spent`, `stats.transaction_count`, and `category_breakdown` reflect the removal without a server restart
- [ ] The deleted row no longer appears in the Transaction History table on `/profile`
- [ ] `/profile`'s Transaction History table shows a "Delete" column to the right of "Edit", with a delete button in every transaction row
- [ ] Clicking a row's delete button triggers a browser confirmation prompt before the request is sent; cancelling the prompt leaves the row intact
- [ ] The delete button's visual style uses `--danger`/`--danger-light` and is visually distinct from the `.btn-primary` Edit/Add Expense buttons
