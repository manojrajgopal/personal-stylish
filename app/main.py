from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pymysql
from sqlalchemy import text

pymysql.install_as_MySQLdb()  # This will make PyMySQL work as MySQLdb

app = Flask(__name__)
app.config['SECRET_KEY'] = 'manoj_rajgopal_1509'

# Configuring the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/fashion'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Dashboard:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        # Define the route for the main dashboard page
        self.app.add_url_rule('/', view_func=self.main, methods=['GET', 'POST'])

    def main(self):
        if request.method == "POST":
            # Handle form submission for email subscription
            email = request.form.get("email")
            if email:
                print(f"New subscription: {email}")
        # Render the main dashboard page
        return render_template('index.html', title='Outfit Recommender')

class Login:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.register_routes()

    def register_routes(self):
        # Define routes for login, signup, and logout
        self.app.add_url_rule('/login', methods=['GET', 'POST'], view_func=self.login)
        self.app.add_url_rule('/signup', methods=['POST'], view_func=self.signup)
        self.app.add_url_rule('/logout', methods=['GET'], view_func=self.logout)

    def login(self):
        if request.method == 'POST':
            # Get username and password from the login form
            username = request.form['username']
            password = request.form['password']

            # Safely execute the query to check login credentials
            query = text('SELECT username, email, phone, name FROM login WHERE username=:username AND password=:password')
            result = self.db.session.execute(query, {'username': username, 'password': password})
            user = result.fetchone()  # Fetch the first matching row

            print(f"Raw user: {user}")  # Debugging: check what is returned

            if user:
                # Store user information in the session
                session['user'] = {'username': user[0], 'email': user[1], 'phone': user[2], 'name':user[3]}  # username = user[0], email = user[1], phone = user[2]
                return redirect(url_for('main'))  # Redirect to the dashboard
            else:
                return render_template('login.html', message="Invalid username or password")

        # Render login page if the request method is GET
        return render_template('login.html', title='Fashion Hub')

    def signup(self):
        # Get user details from the signup form
        name = request.form['name']
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']

        # Check if the username already exists in the database
        check_query = text('SELECT username FROM login WHERE username = :username')
        result = self.db.session.execute(check_query, {'username': username}).fetchone()

        if result:  # If a record is found, the username already exists
            return render_template('login.html', message="Username already exists. Please choose another.", title='Signup')

        # If the username doesn't exist, insert the new user
        insert_query = text('INSERT INTO login (name, username, phone, email, password) VALUES (:name, :username, :phone, :email, :password)')
        self.db.session.execute(insert_query, {
            'name': name,
            'username': username,
            'phone': phone,
            'email': email,
            'password': password
        })
        self.db.session.commit()  # Commit the transaction to the database

        return render_template('login.html', title='Fashion Hub', message="Signup successful! Please log in.")

    def logout(self):
        # Clear the session data and log out the user
        session.pop('user', None)
        return redirect(url_for('main'))  # Redirect to the home page after logging out

class Profile:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        # Define the route for the user profile page
        self.app.add_url_rule('/profile', methods=['GET'], view_func=self.profile)

    def profile(self):
        # Check if the user is logged in (i.e., if 'user' exists in session)
        if 'user' in session:
            # Retrieve user information from the session
            username = session['user']['username']
            email = session['user']['email']
            phone = session['user'].get('phone', 'Not Provided')    # Default value if 'phone' is missing
            name = session['user']['name']  
            return render_template('profile.html', username=username, email=email, phone=phone, name=name)
        else:
            # Redirect to login if the user is not logged in
            return redirect(url_for('login'))

# Initialize the classes
Dashboard(app)
Login(app, db)
Profile(app)

if __name__ == '__main__':
    app.secret_key = 'manojrajgopal15'  # Ensure you have a secret key for sessions
    app.run(debug=True)
