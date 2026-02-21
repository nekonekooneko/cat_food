from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# DB接続関数
def get_db():
    conn = sqlite3.connect("cat_app.db")
    conn.row_factory = sqlite3.Row
    return conn

# テーブル自動作成
def init_db():
    conn = sqlite3.connect("cat_app.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/main")
def main():
    return render_template("main.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        conn.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/pets")
def pets():
    return render_template("pets.html")

@app.route("/pet_new")
def pet_new():
    return render_template("pet_new.html")

@app.route("/food")
def food():
    return render_template("food.html")

@app.route("/food_new")
def food_new():
    return render_template("food_new.html")

if __name__ == "__main__":
    app.run(debug=True)