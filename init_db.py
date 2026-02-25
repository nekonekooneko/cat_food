import sqlite3

DB_NAME = "cat_app.db"

schema = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cats (
    cat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    birth_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS foods (
    food_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    content_amount REAL,
    unit TEXT,
    purchase_link TEXT,
    remaining_amount REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS cat_food_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cat_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    daily_amount REAL DEFAULT 0,
    FOREIGN KEY (cat_id) REFERENCES cats(cat_id),
    FOREIGN KEY (food_id) REFERENCES foods(food_id)
);

CREATE TABLE IF NOT EXISTS feeding_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cat_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    feeding_date TEXT,
    usage_amount REAL,
    memo TEXT,
    FOREIGN KEY (cat_id) REFERENCES cats(cat_id),
    FOREIGN KEY (food_id) REFERENCES foods(food_id)
);
"""

def main():
    conn = sqlite3.connect(DB_NAME)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    main()