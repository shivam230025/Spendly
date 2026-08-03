import random
import sys
from datetime import datetime, timedelta

from database.db import get_db

USER_ID = 2
COUNT = 4
MONTHS = 5

CATEGORIES = [
    ("Food", 50, 800, [
        "Groceries", "Dinner with friends", "Zomato order", "Tiffin service",
        "Street food", "Weekend brunch", "Vegetables and fruits",
    ]),
    ("Transport", 20, 500, [
        "Auto fare", "Ola cab", "Petrol", "Metro card recharge",
        "Bus pass", "Parking fee",
    ]),
    ("Bills", 200, 3000, [
        "Electricity bill", "Mobile recharge", "Broadband bill",
        "Water bill", "Gas cylinder", "DTH recharge",
    ]),
    ("Health", 100, 2000, [
        "Pharmacy", "Doctor consultation", "Gym membership", "Lab tests",
    ]),
    ("Entertainment", 100, 1500, [
        "Movie tickets", "Netflix subscription", "Concert tickets", "Gaming",
    ]),
    ("Shopping", 200, 5000, [
        "New shoes", "Clothing", "Electronics", "Home decor", "Amazon order",
    ]),
    ("Other", 50, 1000, [
        "Miscellaneous", "Gift", "Donation", "Stationery",
    ]),
]

WEIGHTS = [30, 20, 15, 8, 8, 12, 7]


def random_date(months):
    today = datetime.now()
    start = today - timedelta(days=months * 30)
    delta_days = (today - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def generate_expense():
    category, lo, hi, descriptions = random.choices(CATEGORIES, weights=WEIGHTS, k=1)[0]
    amount = round(random.uniform(lo, hi), 2)
    description = random.choice(descriptions)
    date = random_date(MONTHS).strftime("%Y-%m-%d")
    return (USER_ID, amount, category, date, description)


def main():
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE id = ?", (USER_ID,)).fetchone()
    if not user:
        print(f"No user found with id {USER_ID}.")
        conn.close()
        sys.exit(1)

    expenses = [generate_expense() for _ in range(COUNT)]

    try:
        conn.execute("BEGIN")
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            expenses,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    dates = sorted(e[3] for e in expenses)
    print(f"Inserted {len(expenses)} expenses for user_id {USER_ID}.")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    print("Sample records:")
    for e in expenses[:5]:
        print(f"  user_id={e[0]} amount={e[1]} category={e[2]} date={e[3]} description={e[4]!r}")


if __name__ == "__main__":
    main()
