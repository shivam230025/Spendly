import sqlite3

from werkzeug.security import generate_password_hash

DB_PATH = "expense_tracker.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(name, email, password):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email.strip().lower(), generate_password_hash(password)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def create_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def get_expense_by_id(expense_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
    finally:
        conn.close()


def update_expense(expense_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? "
            "WHERE id = ?",
            (amount, category, date, description, expense_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_expenses_by_user(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        query = "SELECT * FROM expenses WHERE user_id = ?"
        params = [user_id]
        if start_date is not None:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date is not None:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_expense_stats(expenses):
    total_spent = sum(row["amount"] for row in expenses)
    transaction_count = len(expenses)
    totals_by_category = {}
    for row in expenses:
        totals_by_category[row["category"]] = totals_by_category.get(row["category"], 0.0) + row["amount"]
    top_category = (
        max(sorted(totals_by_category), key=lambda c: totals_by_category[c])
        if totals_by_category else ""
    )
    return {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category,
    }


def get_category_breakdown(expenses):
    total_spent = sum(row["amount"] for row in expenses)
    if total_spent == 0:
        return []
    totals_by_category = {}
    for row in expenses:
        totals_by_category[row["category"]] = totals_by_category.get(row["category"], 0.0) + row["amount"]
    breakdown = []
    for category in sorted(totals_by_category, key=lambda c: (-totals_by_category[c], c)):
        amount = totals_by_category[category]
        breakdown.append({
            "category": category,
            "amount": amount,
            "percent": round(amount / total_spent * 100),
            "css_class": "bar-" + category.lower(),
        })
    return breakdown


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cursor.lastrowid

    expenses = [
        (user_id, 12.50, "Food", "2026-08-01", "Groceries"),
        (user_id, 45.00, "Transport", "2026-08-02", "Monthly bus pass"),
        (user_id, 89.99, "Bills", "2026-08-03", "Electricity bill"),
        (user_id, 25.00, "Health", "2026-08-05", "Pharmacy"),
        (user_id, 15.75, "Entertainment", "2026-08-08", "Movie tickets"),
        (user_id, 60.20, "Shopping", "2026-08-12", "New shoes"),
        (user_id, 9.00, "Other", "2026-08-15", "Miscellaneous"),
        (user_id, 32.40, "Food", "2026-08-18", "Dinner with friends"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
