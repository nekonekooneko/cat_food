from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3

app = Flask(__name__, static_url_path='/css', static_folder='static')
app.secret_key = "nyans_secret_key"


# ---------------------------
# DB接続
# ---------------------------
def get_db():
    conn = sqlite3.connect("cat_app.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------
# 毎日1回の残量自動引き落とし
# ---------------------------
def deduct_daily_food():
    conn = get_db()

    settings = conn.execute("""
        SELECT c.cat_id, f.food_id,
               f.remaining_amount, s.daily_amount
        FROM cat_food_settings s
        JOIN foods f ON s.food_id = f.food_id
        JOIN cats c ON s.cat_id = c.cat_id
    """).fetchall()

    for s in settings:
        new_remaining = s["remaining_amount"] - s["daily_amount"]
        if new_remaining < 0:
            new_remaining = 0

        conn.execute("""
            UPDATE foods
            SET remaining_amount = ?
            WHERE food_id = ?
        """, (new_remaining, s["food_id"]))

        conn.execute("""
            INSERT INTO feeding_logs (cat_id, food_id, feeding_date, usage_amount, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (
            s["cat_id"],
            s["food_id"],
            datetime.now(),
            s["daily_amount"],
            "自動引き落とし"
        ))

    conn.commit()
    conn.close()


# ---------------------------
# 画面ルート
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/main")
def main():
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    foods = conn.execute("""
        SELECT
            f.food_id,
            f.name,
            f.purchase_link,
            f.remaining_amount,
            s.daily_amount
        FROM foods f
        LEFT JOIN cat_food_settings s ON f.food_id = s.food_id
        WHERE f.user_id = ?
    """, (session["user_id"],)).fetchall()
    conn.close()

    emergency_items = []

    for f in foods:
        daily_amount = f["daily_amount"]

        # ★本来のロジック（テスト終了後ここに戻す）
        if not daily_amount or daily_amount == 0:
            days_left = 999
        else:
            days_left = int(f["remaining_amount"] / daily_amount)

        if days_left <= 3:
            emergency_items.append({
                "food_id": f["food_id"],
                "name": f["name"],
                "purchase_link": f["purchase_link"],
                "days_left": days_left,
                "state": "emergency"
            })

    return render_template(
        "main.html",
        emergency_items=emergency_items,
        countdown_item=None
    )


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
        session["user_id"] = user["user_id"]
        return redirect(url_for("main"))
    else:
        return "メールアドレスまたはパスワードが違います"


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------
# 愛猫
# ---------------------------
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


@app.route("/pet_edit/<int:cat_id>", methods=["GET", "POST"])
def pet_edit(cat_id):
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db()

    if request.method == "POST":
        name = request.form["name"]
        birth_date = request.form["birth_date"]

        conn.execute(
            "UPDATE cats SET name = ?, birth_date = ? WHERE cat_id = ? AND user_id = ?",
            (name, birth_date, cat_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        return redirect(url_for("pets"))

    cat = conn.execute(
        "SELECT * FROM cats WHERE cat_id = ? AND user_id = ?",
        (cat_id, session["user_id"])
    ).fetchone()
    conn.close()

    return render_template("pet_edit.html", cat=cat)


# ---------------------------
# ご飯
# ---------------------------
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
        content_amount = float(request.form["content_amount"])
        unit = request.form["unit"]
        purchase_link = request.form["purchase_link"]

        conn = get_db()
        conn.execute("""
            INSERT INTO foods
            (user_id, name, content_amount, unit, purchase_link, remaining_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            name,
            content_amount,
            unit,
            purchase_link,
            content_amount
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("food"))

    return render_template("food_new.html")


@app.route("/food_edit/<int:food_id>", methods=["GET", "POST"])
def food_edit(food_id):
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db()

    if request.method == "POST":
        name = request.form["name"]
        content_amount = float(request.form["content_amount"])
        unit = request.form["unit"]
        purchase_link = request.form["purchase_link"]

        conn.execute("""
            UPDATE foods
            SET name=?, content_amount=?, unit=?, purchase_link=?
            WHERE food_id=? AND user_id=?
        """, (
            name,
            content_amount,
            unit,
            purchase_link,
            food_id,
            session["user_id"]
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("food"))

    food = conn.execute(
        "SELECT * FROM foods WHERE food_id=? AND user_id=?",
        (food_id, session["user_id"])
    ).fetchone()

    conn.close()

    return render_template("food_edit.html", food=food)


# ---------------------------
# 注文状態管理
# ---------------------------
@app.route("/order_click/<int:food_id>")
def order_click(food_id):
    session[f"food_state_{food_id}"] = "order_confirm"
    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("main"))


@app.route("/order_yes/<int:food_id>", methods=["POST"])
def order_yes(food_id):
    session[f"food_state_{food_id}"] = "waiting_arrival"
    return redirect(url_for("main"))


@app.route("/order_no/<int:food_id>", methods=["POST"])
def order_no(food_id):
    session[f"food_state_{food_id}"] = "emergency"
    return redirect(url_for("main"))


# ---------------------------
# サーバー起動（必ず最後）
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)

    # test