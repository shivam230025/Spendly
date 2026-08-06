import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

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


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "January 2026",
    }

    stats = {
        "total_spent": 289.84,
        "transaction_count": 6,
        "top_category": "Food",
    }

    transactions = [
        {"date": "2026-08-18", "description": "Dinner with friends", "category": "Food", "amount": 32.40},
        {"date": "2026-08-15", "description": "Miscellaneous", "category": "Other", "amount": 9.00},
        {"date": "2026-08-12", "description": "New shoes", "category": "Shopping", "amount": 60.20},
        {"date": "2026-08-08", "description": "Movie tickets", "category": "Entertainment", "amount": 15.75},
        {"date": "2026-08-05", "description": "Pharmacy", "category": "Health", "amount": 25.00},
        {"date": "2026-08-03", "description": "Electricity bill", "category": "Bills", "amount": 89.99},
    ]

    category_breakdown = [
        {"category": "Bills", "amount": 89.99, "percent": 31, "css_class": "bar-bills"},
        {"category": "Shopping", "amount": 60.20, "percent": 21, "css_class": "bar-shopping"},
        {"category": "Transport", "amount": 45.00, "percent": 16, "css_class": "bar-transport"},
        {"category": "Food", "amount": 44.90, "percent": 15, "css_class": "bar-food"},
        {"category": "Health", "amount": 25.00, "percent": 9, "css_class": "bar-health"},
        {"category": "Entertainment", "amount": 15.75, "percent": 5, "css_class": "bar-entertainment"},
        {"category": "Other", "amount": 9.00, "percent": 3, "css_class": "bar-other"},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        category_breakdown=category_breakdown,
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
