import sqlite3
from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_expenses_by_user,
    get_expense_stats,
    get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

DUMMY_PASSWORD_HASH = generate_password_hash("dummy-password-for-timing-safety")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password or not confirm_password:
        flash("All fields are required.")
        return render_template("register.html")

    if password != confirm_password:
        flash("Passwords do not match.")
        return render_template("register.html")

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        flash("Email already registered.")
        return render_template("register.html")

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = get_user_by_email(email)

    if user is None:
        check_password_hash(DUMMY_PASSWORD_HASH, password)
        flash("Invalid email or password.")
        return render_template("login.html")

    if not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.")
        return render_template("login.html")

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _initials_from_name(name):
    parts = name.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _format_member_since(created_at):
    return datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%B %Y")


def _resolve_date_range(args):
    range_value = args.get("range", "")

    if range_value == "this_month":
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        return start, end, {"range": "this_month", "start_date": "", "end_date": ""}

    if range_value in ("3m", "6m"):
        days = 90 if range_value == "3m" else 180
        today = date.today()
        start = (today - timedelta(days=days)).isoformat()
        end = today.isoformat()
        return start, end, {"range": range_value, "start_date": "", "end_date": ""}

    if range_value == "custom":
        start_raw = args.get("start_date", "")
        end_raw = args.get("end_date", "")
        try:
            start_dt = datetime.strptime(start_raw, "%Y-%m-%d")
            end_dt = datetime.strptime(end_raw, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date range. Showing all transactions instead.")
            return None, None, {"range": "", "start_date": "", "end_date": ""}

        if start_dt > end_dt:
            flash("Start date must be before end date. Showing all transactions instead.")
            return None, None, {"range": "", "start_date": "", "end_date": ""}

        return start_raw, end_raw, {"range": "custom", "start_date": start_raw, "end_date": end_raw}

    return None, None, {"range": "", "start_date": "", "end_date": ""}


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    db_user = get_user_by_id(user_id)

    user = {
        "name": db_user["name"],
        "email": db_user["email"],
        "initials": _initials_from_name(db_user["name"]),
        "member_since": _format_member_since(db_user["created_at"]),
    }

    start_date, end_date, filters = _resolve_date_range(request.args)
    expense_rows = get_expenses_by_user(user_id, start_date=start_date, end_date=end_date)
    stats = get_expense_stats(expense_rows)
    category_breakdown = get_category_breakdown(expense_rows)
    transactions = [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
        }
        for row in expense_rows
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        category_breakdown=category_breakdown,
        filters=filters,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
