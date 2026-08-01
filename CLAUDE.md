# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is a Flask-based expense tracking application. The project is structured as a learning exercise with placeholder routes that are meant to be implemented progressively. The app includes a landing page, user authentication flows (register/login), and infrastructure for tracking expenses.

**Tech Stack:**
- Flask 3.1.3 (lightweight Python web framework)
- Werkzeug 3.1.6 (WSGI utilities for Flask)
- SQLite (database, referenced in `.gitignore` as `expense_tracker.db`)
- Pytest 8.3.5 & pytest-flask 1.3.0 (testing)
- HTML/CSS/JavaScript for frontend

## Common Development Commands

**Setup (one-time):**
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run the development server:**
```bash
source venv/Scripts/activate  # Activate virtual environment first
python app.py
```
The app runs at `http://127.0.0.1:5001` with debug mode enabled (auto-reloads on file changes).

**Run tests:**
```bash
pytest
```

**Run a single test file:**
```bash
pytest tests/test_auth.py -v
```

**Note:** Each bash/shell command starts fresh. If using separate commands, either:
- Activate venv once: `source venv/Scripts/activate`, then run subsequent commands in the same session
- Or use the venv's Python directly: `venv/Scripts/python.exe app.py` (no activation needed)

## Project Structure

```
expense-tracker/
├── app.py                      # Main Flask application with route definitions
├── requirements.txt            # Python dependencies (Flask, Werkzeug, pytest, pytest-flask)
├── database/
│   ├── __init__.py            # Empty module marker
│   └── db.py                  # Database functions (students implement: get_db, init_db, seed_db)
├── templates/
│   ├── base.html              # Base template with navbar, footer, common layout
│   ├── landing.html           # Landing/home page
│   ├── register.html          # User registration form
│   └── login.html             # User login form
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet (comprehensive design system)
│   └── js/
│       └── main.js            # JavaScript (students add code here)
└── venv/                       # Virtual environment (in .gitignore)
```

## Architecture & Key Concepts

**Flask App Structure (app.py):**
- Flask app initialized at `app = Flask(__name__)` with debug mode enabled on port 5001
- Route-based architecture using `@app.route()` decorators
- Routes return HTML templates via `render_template()`

**Routes (Current & Placeholder):**
- `GET /` — Landing page (implemented)
- `GET /register` — Register form (implemented)
- `GET /login` — Login form (implemented)
- `GET /logout` — Logout (placeholder: "Logout — coming in Step 3")
- `GET /profile` — User profile (placeholder: "Profile page — coming in Step 4")
- `GET /expenses/add` — Add expense form (placeholder: "Add expense — coming in Step 7")
- `GET /expenses/<id>/edit` — Edit expense (placeholder: "Edit expense — coming in Step 8")
- `GET /expenses/<id>/delete` — Delete expense (placeholder: "Delete expense — coming in Step 9")

**Database Layer (database/db.py):**
Students implement three functions:
- `get_db()` — Returns SQLite connection with row_factory and foreign keys enabled
- `init_db()` — Creates tables using `CREATE TABLE IF NOT EXISTS`
- `seed_db()` — Inserts sample data for development

The app expects a SQLite database file at the root (`expense_tracker.db`).

**Templates:**
- `base.html` — Master template with navigation, footer, and Jinja2 block structure
- Child templates inherit from `base.html` and override `{% block content %}`
- Navigation links use Flask's `url_for()` helper for dynamic URL generation

**Styling:**
- Single `style.css` file with CSS variables (--ink, --accent, --paper, etc.)
- Responsive design with sections for navbar, hero, features, auth forms, footer
- DM Serif Display (headings) and DM Sans (body) fonts from Google Fonts
- Design targets 1200px max-width for content, 440px for auth forms

**Frontend:**
- `main.js` is a placeholder; students add interactivity here

## Development Notes

- **Debug Mode:** Enabled by default. The Werkzeug debugger runs on `http://127.0.0.1:5001/` with a PIN.
- **.gitignore:** Excludes `venv/`, `expense_tracker.db`, `__pycache__/`, `*.pyc`, `*.pyo`, `.env`, `.DS_Store`, `.claude/plans/`
- **Testing:** Use pytest for unit tests. pytest-flask provides fixtures for testing Flask routes.
- **No existing database:** The app expects students to implement database setup in `database/db.py`.

## Next Steps for Development

1. Implement `database/db.py` (schema definition, connection management, seed data)
2. Add form submission handlers for register/login (currently just render templates)
3. Implement placeholder routes (logout, profile, add/edit/delete expense)
4. Build out the expense management UI (forms, lists, editing)
5. Add JavaScript interactivity in `static/js/main.js`