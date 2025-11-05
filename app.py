from flask import Flask, render_template, request, redirect, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voter_id TEXT UNIQUE,
        name TEXT,
        password TEXT,
        has_voted INTEGER DEFAULT 0
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        votes INTEGER DEFAULT 0
    )''')

    conn.commit()
    conn.close()

init_db()

def seed_candidates():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM candidates")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO candidates (name) VALUES ('Candidate A'), ('Candidate B'), ('Candidate C')")
    conn.commit()
    conn.close()

seed_candidates()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        name = request.form["name"]
        password = request.form["password"]   # NEW PASSWORD FIELD

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (voter_id, name, password) VALUES (?, ?, ?)", 
                        (voter_id, name, password))
            conn.commit()
            flash("Registration Successful. Please Login!", "success")
            return redirect("/login")
        except:
            flash("Voter ID already exists!", "danger")

        conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE voter_id=? AND password=?", (voter_id, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["voter_id"] = voter_id

            # Already voted → move to already voted page
            if user[4] == 1:
                return redirect("/already_voted")

            flash("Login Successful!", "success")
            return redirect("/vote")
        else:
            flash("Invalid Voter ID or Password!", "danger")
            return redirect("/login")

    return render_template("login.html")

@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter_id" not in session:
        flash("Please login first!", "warning")
        return redirect("/login")

    voter_id = session["voter_id"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT has_voted FROM users WHERE voter_id=?", (voter_id,))
    has_voted = cur.fetchone()[0]

    if has_voted == 1:
        return redirect("/already_voted")

    cur.execute("SELECT * FROM candidates")
    candidates = cur.fetchall()

    if request.method == "POST":
        candidate_id = request.form["candidate"]

        cur.execute("UPDATE candidates SET votes = votes + 1 WHERE id=?", (candidate_id,))
        cur.execute("UPDATE users SET has_voted = 1 WHERE voter_id=?", (voter_id,))
        conn.commit()
        conn.close()

        return redirect("/thankyou")

    conn.close()
    return render_template("vote.html", candidates=candidates)

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@app.route("/already_voted")
def already_voted():
    return render_template("already_voted.html")

@app.route("/results")
def results():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates ORDER BY votes DESC")
    results = cur.fetchall()
    conn.close()
    return render_template("results.html", results=results)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
