import sqlite3

DB_NAME = "cat_app.db"

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table});")
    return any(row[1] == column for row in cur.fetchall())

def main():
    conn = sqlite3.connect(DB_NAME)

    # foods に remaining_amount が無ければ追加
    if not column_exists(conn, "foods", "remaining_amount"):
        conn.execute("ALTER TABLE foods ADD COLUMN remaining_amount REAL DEFAULT 0;")
        conn.commit()
        print("Added column: foods.remaining_amount")
    else:
        print("foods.remaining_amount already exists")

    conn.close()

if __name__ == "__main__":
    main()