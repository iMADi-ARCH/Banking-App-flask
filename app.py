from flask import Flask, render_template, jsonify, request
import mysql.connector as my
import pandas as pd

app = Flask(__name__)

try:
    con = my.connect(host='localhost', user='root',
                     passwd='', database='bank')
    cur = con.cursor()
except my.errors.DatabaseError:
    print('Server Connection Failed')

# app.url_for('static', filename='style.css')
# SERVER_NAME = "bank"
logged_user_data = None


def log_user_in(accno, passwd):
    global logged_user_data
    d = None
    if accno and passwd:
        q = f"SELECT * FROM users WHERE accno='{accno}' and passwd='{passwd}';"
        logged_user_data = pd.read_sql(q, con)
        if not logged_user_data.empty:
            logged_user_data = logged_user_data.iloc[0, :].to_dict().copy()
            print(logged_user_data)
            print("Logged In as", logged_user_data["name"][0] + ".")
    return logged_user_data


def add_amnt(amt):
    """
    "Adds" a given amount to the balance of the logged in user.
    Can also be negative.
    """
    global logged_user_data
    newamt = logged_user_data['balance'] + amt
    accno = logged_user_data['accno']
    # update sql
    q = f"UPDATE users SET balance={newamt} WHERE accno={accno};"
    # update df
    logged_user_data['balance'] = newamt
    cur.execute(q)
    con.commit()
    return newamt


@app.route("/")
def home():
    return render_template("mainmenu.html", logged_user_data=logged_user_data)


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        r = log_user_in(request.form['accno'], request.form['passwd'])
        if not r:
            error = "Invalid Credentials."
    return render_template('login.html', error=error, logged_user_data=logged_user_data)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    error = None
    success = None
    if request.method == "POST":
        accno = request.form['accno']
        name = request.form['name']
        branch = request.form['branch'] or "PAT"
        passwd = request.form['passwd']
        q = f"""
        INSERT INTO
            users (accno, name, passwd, branch)
        VALUES
            ({accno}, '{name}', '{passwd}', "{branch}")
        """
        try:
            cur.execute(q)
            con.commit()
            success = "User created successfully. Login to continue."
        except Exception as e:
            print(e)
            error = "Invalid details please try again."
    return render_template("signup.html", error=error, success=success, logged_user_data=logged_user_data)


@app.route('/personal')
def personal():
    return render_template("personal.html", logged_user_data=logged_user_data)


@app.route('/deposit', methods=["POST", "GET"])
def deposit():
    error = None
    am = 0
    newam = None
    if request.method == "POST":
        am = int(request.form['dpam'])
        newam = add_amnt(am)
    return render_template("deposit.html", error=error, am=am, newam=newam)


@app.route('/withdraw', methods=["POST", "GET"])
def withdraw():
    error = None
    am = 0
    newam = None
    if request.method == "POST":
        am = int(request.form['wtam'])
        newam = logged_user_data['balance'] - am
        if newam < 0:
            error = "Not enough balance."
        else:
            add_amnt(-am)
    return render_template("deposit.html", error=error, am=am, newam=newam)
