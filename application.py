import os
import re

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from helpers import apology, login_required, lookup, usd

# import model class name from models.py
from models import *

# for loading the environmental variables
load_dotenv()


# Configure application
app = Flask(__name__)

#SqlAlchemy Database Configuration With PostgreSQL
DATABASE_URL = os.getenv("DB_URI")
app.config['SQLALCHEMY_DATABASE_URI'] =  DATABASE_URL

# create an object of SQLAlchemy named as db, which will handle our ORM-related activities.
db = SQLAlchemy(app)

# to execute the raw sql queries
db2 =create_engine(DATABASE_URL)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # retrieve all the stocks the current user has
    stocks = Share.query.filter_by(user_id=session["user_id"]).all()

    shares=[]
    for row in stocks:
        shares.append({"shares_name":row.shares_name,"shares_no":float(row.shares_no)})

  
    # retrieve the details of the current_user
    user_details = db2.execute("SELECT * FROM users WHERE id=(%s);",(session["user_id"]))
    

    # to store the cash the user currently has
    for user in user_details:
        current_cash = float(user["cash"])
        
    # to store the current details of the stock symbol by calling the IEX cloud API
    api_results =[]
    for symbol in stocks:
        result = lookup(symbol.shares_name)
        api_results.append(result)

    # to store the sum of the price of the shares the current user has
    sum_of_shares_row = db2.execute("SELECT SUM(total_price) FROM shares WHERE user_id=(%s);",(session["user_id"]))
    for row in sum_of_shares_row:
        sum_of_shares = (re.findall('\d*\.?\d+',str(row)))
 
    if len(sum_of_shares) == 0:
        sum_shares = 0
    else:
        sum_shares = float(sum_of_shares[0])

    return render_template("index.html",stocks=shares, current_cash=current_cash, api_results=api_results,sum_shares=sum_shares)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    #user reached route by POST (as by clicking a link or via redirect)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Ensure no. of shares is a positive integer
        elif int(request.form.get("shares")) <= 0:
            return apology("must provide shares", 403)

        # retrive the details of the current stock symbol
        results = lookup(request.form.get("symbol"))

        if results is None:
            return apology("Invalid symbol", 400)
        else:
            # to look up stock's current price
            current_price = results["price"]

            # to check how much cash the current user has
            user_details = db2.execute("SELECT * FROM users WHERE id=(%s);",(session["user_id"]))
            
            for user in user_details:
                cash = float(user["cash"])
        
            # Ensure the user can afford the no. of shares at the current price
            total_price = current_price * int(request.form.get("shares"))
            if not total_price <= cash:
                return apology("can't afford", 400)

            else:
                cash = float(cash) - total_price

                # update the remaining cash
                db2.execute("UPDATE users SET cash =(%s) WHERE id=(%s);",(cash,session["user_id"]))
               
                # insert the shares pertaining to the current user
                share=Share(
                    user_id=session["user_id"],
                    shares_name=request.form.get("symbol"),
                    shares_no=int(request.form.get("shares")),
                    total_price=total_price
                )
                db.session.add(share)
                db.session.commit()

                # insert the shares pertaining to the current user in the history table
                history=History(
                    user_id=session["user_id"],
                    shares_name=request.form.get("symbol"),
                    shares_no=int(request.form.get("shares")),
                    price=results["price"],
                    status="buy"
                )
                db.session.add(history)
                db.session.commit()

                # Redirect user to home page
                return redirect("/")    

    #user reached route by GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # retrieve all the transactions the current user has in the history table
    history = History.query.filter_by(user_id=session["user_id"]).all()

    return render_template("history.html",history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = User.query.filter_by(username=request.form.get("username")).first()

        # Ensure username  exists and password is correct
        if rows == None or not check_password_hash(rows.hash, request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    #user reached route by POST (as by clicking a link or via redirect)
    if request.method == "POST":
        results = lookup(request.form.get("symbol"))

        if results is None:
            return apology("Invalid symbol", 400)
        else:
            return render_template("quoted.html",results = results)

    #user reached route by GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""


    # user reached route by POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure the username is unique
        rows = User.query.filter_by(username=request.form.get("username")).first() 
      
        if rows != None:
            # username already exists
            return apology("username already exists", 403)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        if not request.form.get("confirmation"):
            return apology("must provide password", 403)

        # Ensure both the passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
        # compiling regex
        regex = re.compile(reg)

        # searching regex
        check_password = re.search(regex, request.form.get("password"))

        if not check_password:
            return apology("passwords must be a combination of uppercase,lowercase,numbers and symbols", 403)

        # insert the data into the users table
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))

        user=User(
            username=username,
            hash=hash,
            cash=10000
        )
        db.session.add(user)
        db.session.commit()

        # Redirect user to home page
        return redirect("/")

    # user reached route by GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # retreive the shares of the logged in user 
    stocks = Share.query.filter_by(user_id=session["user_id"]).all()        

    #user reached route by POST (as by clicking a link or via redirect)
    if request.method == "POST":

        # Ensure the stock symbol was submitted in the form
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Ensure no. of shares(i/p taken from form) is a positive integer
        elif int(request.form.get("shares")) <= 0:
            return apology("must provide shares", 400)

        # retrieve the no. of shares the user has pertaining to the stock symbol
        no_of_shares = db2.execute("SELECT shares_no FROM shares WHERE user_id=(%s) and shares_name=(%s)",(session["user_id"],request.form.get("symbol")))
        
        # extracting the no_of_shares from the result
        for no in no_of_shares:
            no_of_shares = (re.findall('\d*\.?\d+',str(no)))

        # Ensure the user can sell the shares
        if int(request.form.get("shares")) > int(no_of_shares[0]):
            return apology("too many shares",400)

        # update the no. of shares after the user sells in the database
        updated_no_of_shares = int(no_of_shares[0]) - int(request.form.get("shares"))

        db2.execute("UPDATE shares SET shares_no=(%s) WHERE user_id=(%s) AND shares_name=(%s);",(updated_no_of_shares,session["user_id"],request.form.get("symbol")))

        # look up for the details of the stock symbol the users selects
        results = lookup(request.form.get("symbol"))

        # price of the share the user sells
        total_price = results["price"] * int(request.form.get("shares"))

        db2.execute("UPDATE shares SET total_price=(%s) WHERE user_id=(%s) and shares_name=(%s);",(total_price,session["user_id"],request.form.get("symbol")))

        # retrieve details of the current user
        user_details = db2.execute("SELECT * FROM users WHERE id=(%s);",(session["user_id"]))
            
        # how much cash the user has prior selling
        for user in user_details:
            current_cash = float(user["cash"])

        update_current_cash = float(current_cash) + total_price

        db2.execute("UPDATE users SET cash=(%s) WHERE id=(%s);",(update_current_cash,session["user_id"]))

        # insert the shares pertaining to the current user in the history table
        history=History(
                    user_id=session["user_id"],
                    shares_name=request.form.get("symbol"),
                    shares_no=int(request.form.get("shares")),
                    price=results["price"],
                    status="sell"
                )
        db.session.add(history)
        db.session.commit()
        
        # Redirect user to home page
        return redirect("/")

    #user reached route by GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html",stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)



if __name__ == "__main__":
    app.run(debug=True)