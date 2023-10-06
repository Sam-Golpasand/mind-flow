import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import requests
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

from helpers import apology, login_required

app = Flask(__name__)
conn = sqlite3.connect("users.db")

c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);""")
c.execute("""CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, content TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id));""")

conn.commit()


# Configure the session settings
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'my_secret_key'

Session(app)

@app.route("/")
@login_required
def index():
    user_id = session["user_id"]

    category = 'success'
    api_url = 'https://api.api-ninjas.com/v1/quotes?category={}'.format(category)
    response = requests.get(api_url, headers={'X-Api-Key': '63RLHgE/Zdo1I8Vh9xcgJg==N1y5jgJJlmYGMamt'})
    
    if response.status_code == requests.codes.ok:
        data = response.json()  # Parse the response JSON data
        if data:
            first_item = data[0]
            quote = first_item["quote"]
            author = first_item["author"]
        else:
            quote = "No quotes available"  # Set a default quote if no quotes are available
            author = "Unknown"  # Set a default author if fetching failed
    else:
        print("Error:", response.status_code, response.text)
        quote = "Failed to fetch quote"  # Set a default quote if fetching failed
        author = "Unknown"  # Set a default author if fetching failed


    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()

    if row is not None:
        username = row[0]
    else:
        username = "Unknown"  # Set a default username if not found

    conn.close()
    
    return render_template("index.html", username=username, quote=quote, author=author)

@app.route("/meditation")
@login_required
def meditation():
  user_id = session["user_id"]
  return render_template("meditation.html")
  

@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    if request.method == "POST":
        user_id = session["user_id"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()

        if row is not None:
            username = row[0]
        else:
            username = "Unknown"  # Set a default username if not found

        content = request.form.get("content")

        if content is None:
            return apology("You have to write something in the journal")
        else:
            c.execute("INSERT INTO journal (user_id, content) VALUES (?, ?)", (user_id, content))
            conn.commit()

            
        c.execute("SELECT content, timestamp FROM journal WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        journals = c.fetchall()
        return render_template("journal.html", username=username, journals=journals)
    else:
        user_id = session["user_id"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()

        if row is not None:
            username = row[0]
        else:
            username = "Unknown"  # Set a default username if not found

        c.execute("SELECT content, timestamp FROM journal WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        journals = c.fetchall()

        conn.close()
        return render_template("journal.html", username=username, journals=journals)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("You must provide a username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("You must provide a password", 400)

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = c.fetchone()  # Fetch the first row from the cursor

        if row is None or not check_password_hash(row[2], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = int(row[0])

        conn.commit()
        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if (request.method == "POST"):
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("The username field is empty", 400)
        elif not password:
            return apology("The password field is empty", 400)
        elif not confirmation:
            return apology("The confirmation field is empty", 400)

        if password != confirmation:
            return apology("The password and confirmation doesn't match", 400)

        token = generate_password_hash(password)

        conn = sqlite3.connect("users.db")
        c = conn.cursor()


        try:
            c.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, token))
            conn.commit()
            return redirect("/")
        except Exception as e: print(e)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


if __name__ == "__main__":
  app.run()
