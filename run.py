from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3


app = Flask(__name__)
app.secret_key = "nyans_secret_key"

# DB接続関数
def get_db():
    conn = sqlite3.connect("cat_app.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/main")
def main():
    if "user_id" not in session:
        return redirect(url_for("index"))
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

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password)
    ).fetchone()
    conn.close()

    if user:
        session["user_id"] = user["user_id"]  # ← 追加
        return redirect(url_for("main"))
        print(user.keys())
    else:
        return "メールアドレスまたはパスワードが違います"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/pets")
def pets():
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cats = conn.execute(
        "SELECT * FROM cats WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("pets.html", cats=cats)

@app.route("/pet_new", methods=["GET", "POST"])
def pet_new():
    if "user_id" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form["name"]
        birth_date = request.form["birth_date"]

        conn = get_db()
        conn.execute(
            "INSERT INTO cats (user_id, name, birth_date) VALUES (?, ?, ?)",
            (session["user_id"], name, birth_date)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("pets"))

    return render_template("pet_new.html")

@app.route("/food")
def food():
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    foods = conn.execute(
        "SELECT * FROM foods WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("food.html", foods=foods)

@app.route("/food_new", methods=["GET", "POST"])
def food_new():
    if "user_id" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form["name"]
        content_amount = request.form["content_amount"]
        unit = request.form["unit"]
        purchase_link = request.form["purchase_link"]

        conn = get_db()
        conn.execute(
            """
            INSERT INTO foods (user_id, name, content_amount, unit, purchase_link)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session["user_id"], name, content_amount, unit, purchase_link)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("food"))

    return render_template("food_new.html")

if __name__ == "__main__":
    app.run(debug=True)