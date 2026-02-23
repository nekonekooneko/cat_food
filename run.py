from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

import sqlite3


app = Flask(__name__, static_url_path='/css', static_folder='static')
app.secret_key = "nyans_secret_key"

# DB接続関数
def get_db():
    conn = sqlite3.connect("cat_app.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------
# 毎日1回の残量自動引き落とし
# ---------------------------
def deduct_daily_food():
    conn = get_db()

    # 1. cat_food_settings から user ごとの daily_amount と foods を取得
    settings = conn.execute("""
        SELECT c.cat_id, c.name AS cat_name, f.food_id, f.name AS food_name,
               f.remaining_amount, s.daily_amount
        FROM cat_food_settings s
        JOIN foods f ON s.food_id = f.food_id
        JOIN cats c ON s.cat_id = c.cat_id
    """).fetchall()

    for s in settings:
        new_remaining = s["remaining_amount"] - s["daily_amount"]
        if new_remaining < 0:
            new_remaining = 0  # 残量がマイナスにならないように

        # 2. foods テーブルを更新
        conn.execute("""
            UPDATE foods
            SET remaining_amount = ?
            WHERE food_id = ?
        """, (new_remaining, s["food_id"]))

        # 3. feeding_logs にも記録
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
    print("今日の自動残量引き落としが完了しました。")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/main")
def main():
    if "user_id" not in session:
        return redirect(url_for("index"))

    conn = get_db()

    foods = conn.execute("""
        SELECT f.food_id, f.name, f.purchase_link,
               f.remaining_amount, s.daily_amount
        FROM foods f
        JOIN cat_food_settings s ON f.food_id = s.food_id
        JOIN cats c ON s.cat_id = c.cat_id
        WHERE f.user_id = ?
    """, (session["user_id"],)).fetchall()



    conn.close()

    # ★UI確認用のダミーデータ（あとでDB連携に差し替える）
    emergency_items = []

    for f in foods:
        daily_amount = f["daily_amount"]

        if not daily_amount or daily_amount == 0:
            days_left = 999
        else:
            days_left = int(f["remaining_amount"] / daily_amount)

        food_id = f["food_id"]

        # 在庫3日以下なら emergency
        if days_left <= 3:
            emergency_items.append({
                "food_id": food_id,
                "name": f["name"],
                "purchase_link": f["purchase_link"],
                "days_left": days_left,
                "state": "emergency"
            })

        # もしくは state が進行中なら表示
        else:
            state = session.get(f"food_state_{food_id}", None)

            if state in ["order_confirm", "waiting_arrival"]:
                emergency_items.append({
                    "food_id": food_id,
                    "name": f["name"],
                    "purchase_link": f["purchase_link"],
                    "days_left": days_left,
                    "state": state
                })

    return render_template(
        "main.html",
        emergency_items=emergency_items,
        countdown_item=None) # 今は緊急表示のUI確認が目的なので None 固定

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
        content_amount = float(request.form["content_amount"])
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

@app.route("/run_daily_deduction")
def run_daily_deduction():
    deduct_daily_food()
    return "残量の自動引き落としを実行しました"
    
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

# ★stateのリセット：/reset_state/1にアクセスすると food_id=1 の状態をリセット（状態なし）に戻す
@app.route("/reset_state/<int:food_id>")
def reset_state(food_id):
    session.pop(f"food_state_{food_id}", None)
    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(debug=True)