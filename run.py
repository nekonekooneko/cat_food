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

    # ★UI確認用のダミーデータ（あとでDB連携に差し替える）
    base_items = [
        {"food_id": 1, "name": "ご飯A", "purchase_link": "https://example.com/a", "days_left": 2},
        {"food_id": 2, "name": "ご飯B", "purchase_link": "https://example.com/b", "days_left": 1},
    ]

    # ★foodごとの状態を session から反映（無ければ emergency 扱い）
    emergency_items = []
    for item in base_items:
        food_id = item["food_id"]
        state = session.get(f"food_state_{food_id}", "emergency")
        emergency_items.append({**item, "state": state})

    countdown_item = None  # 今は緊急表示のUI確認が目的なので None 固定

    return render_template(
        "main.html",
        emergency_items=emergency_items,
        countdown_item=countdown_item
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
        # ★列名を必ず確認できるように出す（VSCodeターミナルに表示されます）
        print("user columns:", user.keys())

        # ★DBの設計差を吸収：よくある主キー名候補を順に試す
        user_id_value = None
        for key in ("user_id", "id", "users_id"):
            if key in user.keys():
                user_id_value = user[key]
                break

        if user_id_value is None:
            return "ユーザーID列が見つかりません。ターミナルの user columns を確認してください。"

        session["user_id"] = user_id_value
        return redirect(url_for("main"))
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

# ★注文ボタン押下 → 状態②（注文確認）へ + 外部サイトへ遷移
@app.route("/order_click/<int:food_id>")
def order_click(food_id):
    session[f"food_state_{food_id}"] = "order_confirm"
    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("main"))

# ★注文確認：「はい」→ 状態③（到着待ち）
@app.route("/order_yes/<int:food_id>", methods=["POST"])
def order_yes(food_id):
    session[f"food_state_{food_id}"] = "waiting_arrival"
    return redirect(url_for("main"))

# ★注文確認：「いいえ」→ 状態①（緊急）に戻す
@app.route("/order_no/<int:food_id>", methods=["POST"])
def order_no(food_id):
    session[f"food_state_{food_id}"] = "emergency"
    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(debug=True)