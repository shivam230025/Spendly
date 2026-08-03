import random
import sys
from datetime import datetime

from werkzeug.security import generate_password_hash

from database.db import get_db, init_db

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya",
    "Arjun", "Divya", "Karthik", "Meera", "Suresh", "Pooja", "Nikhil", "Isha",
    "Deepak", "Ritu", "Manoj", "Shreya", "Aditya", "Neha", "Sanjay", "Aishwarya",
    "Varun", "Lakshmi", "Harish", "Swati", "Gaurav", "Nandini",
]

LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Nair", "Reddy", "Gupta", "Menon", "Rao",
    "Patel", "Singh", "Kumar", "Chatterjee", "Mukherjee", "Pillai", "Joshi",
    "Desai", "Bhat", "Kulkarni", "Agarwal", "Chauhan",
]


def generate_user():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    suffix = random.randint(10, 999)
    email = f"{first.lower()}.{last.lower()}{suffix}@gmail.com"
    return name, email


def main():
    init_db()
    conn = get_db()

    while True:
        name, email = generate_user()
        existing = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone()
        if not existing:
            break

    password_hash = generate_password_hash("password123")
    created_at = datetime.now().isoformat(sep=" ", timespec="seconds")

    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, created_at),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    print("User created:")
    print(f"  id:    {user_id}")
    print(f"  name:  {name}")
    print(f"  email: {email}")


if __name__ == "__main__":
    main()
