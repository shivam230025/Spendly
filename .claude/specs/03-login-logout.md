# Spec: Login And Logout

## Overview
Implement session-based authentication so registered users can sign in and out of Spendly. This step upgrades the existing stub `GET /login` route into a full login flow (validate credentials, start a session) and replaces the `GET /logout` placeholder with logic that ends the session. This is the mechanism that turns the app from "anyone can view any page" into "some pages require a signed-in user," and it is a prerequisite for Step 04 (profile) and every expense-management route that follows.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (`create_user()`, existing users to log in as)

## Routes
- `GET /login` — render login form — public (already exists as stub, upgrade it)
- `POST /login` — validate email/password, start session, redirect to `/profile` — public
- `GET /logout` — clear session, redirect to `/` — logged-in (safe to hit while logged out too; just redirects)

## Database changes
No new tables or columns. The existing `users` table (id, name, email, password_hash, created_at) covers all requirements.

A new DB helper must be added to `database/db.py`:
- `get_user_by_email(email)` — runs a parameterised `SELECT * FROM users WHERE email = ?`, returns the row (or `None` if not found).

## Templates
- **Modify:** `templates/login.html`
  - Change the form `action` to `url_for('login')` (keep `method="POST"`)
  - Add `name` attributes already present on inputs — confirm `email`/`password` match `request.form.get()` keys
  - Replace the existing `{% if error %}...{% endif %}` block with flash-based rendering (`{% with messages = get_flashed_messages() %}`), consistent with the pattern used in `register.html` from Step 02
- **Modify:** `templates/base.html`
  - Nav links must reflect session state: when logged out, show "Sign in" / "Get started" (current behavior); when logged in, show a "Sign out" link (`url_for('logout')`) instead. Wrap the existing nav-links block in `{% if session.user_id %}...{% else %}...{% endif %}`

## Files to change
- `app.py` — upgrade `login()` to handle `GET` and `POST`; implement `logout()`; import `session` from flask
- `database/db.py` — add `get_user_by_email()` helper
- `templates/login.html` — wire up form action, flash message display
- `templates/base.html` — conditional nav based on `session.user_id`

## Files to create
None.

## New dependencies
No new dependencies. Uses `werkzeug.security.check_password_hash` (already installed) and Flask's built-in `session` / `flash` / `redirect` / `url_for`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use f-strings in SQL
- Passwords hashed with werkzeug — verify with `werkzeug.security.check_password_hash`, never compare plaintext
- If no user is found, still run check_password_hash() against a dummy/precomputed hash before flashing the error, to keep response time consistent between the two failure paths.
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `app.secret_key` is already set in `app.py` (from Step 02) — reuse it, do not add a second secret key
- On `POST /login`:
  1. Look up the user by email with `get_user_by_email()`
  2. If no user found, or `check_password_hash()` fails, flash a single generic error ("Invalid email or password") — do not reveal whether the email exists
  3. On success, store `session["user_id"] = user["id"]` and redirect to `url_for('profile')`
  4. On any failure, re-render the login form with the flashed error — do not redirect
- `GET /logout` must call `session.clear()` (or `session.pop("user_id", None)`) then `redirect(url_for('landing'))`, regardless of whether a session existed
- Call session.clear() before setting session["user_id"] on successful login, to avoid session fixation from a pre-existing (possibly attacker-supplied) session.
- Use `abort(405)` if an unsupported HTTP method reaches `/login`
- Normalize email to lowercase (and strip whitespace) before calling get_user_by_email() — must match the normalization used in registration.
- Do not implement a `login_required` decorator or protect `/profile` / `/expenses/*` routes in this step — that belongs to later steps; this step only establishes the session and the logout mechanism
- Use `url_for()` for every internal link — never hardcode URLs
- if a logged-in user visits `GET /login` , redirect them to `/profile`.

## Definition of done
- [ ] `GET /login` renders the login form without errors
- [ ] Submitting valid credentials for the seeded demo user (`demo@spendly.com` / `demo123`) redirects to `/profile` and sets a session cookie
- [ ] Submitting an unknown email re-renders the form with "Invalid email or password", no session set
- [ ] Submitting a known email with the wrong password re-renders the form with "Invalid email or password", no session set
- [ ] After a successful login, the navbar shows "Sign out" instead of "Sign in" / "Get started"
- [ ] Visiting `/logout` while logged in clears the session and redirects to `/`, after which the navbar shows "Sign in" / "Get started" again
- [ ] Visiting `/logout` while logged out does not error — it redirects to `/` cleanly
