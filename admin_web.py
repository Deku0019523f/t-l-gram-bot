import os
import sqlite3
from flask import Flask, request, render_template_string
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1299831974
bot = Bot(BOT_TOKEN)
app = Flask(__name__)

DATABASE = "users.db"

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        message = request.form.get("message")
        if message:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM users")
            users = cursor.fetchall()
            for (uid,) in users:
                try:
                    bot.send_message(chat_id=uid, text=message)
                except:
                    continue
            conn.close()
            return "Message envoyé !"
    user_count = get_user_count()
    return render_template_string("""
        <h2>Interface Admin</h2>
        <p>Utilisateurs enregistrés : {{ user_count }}</p>
        <form method="post">
            <textarea name="message" rows="4" cols="50"></textarea><br>
            <button type="submit">Envoyer à tous</button>
        </form>
    """, user_count=user_count)

def get_user_count():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER)")
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
