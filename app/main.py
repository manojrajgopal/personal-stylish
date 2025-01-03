from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pymysql
from sqlalchemy import text
from datetime import datetime

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
            query = text('SELECT username, email, phone, name, password FROM login WHERE username=:username AND password=:password')
            result = self.db.session.execute(query, {'username': username, 'password': password})
            user = result.fetchone()  # Fetch the first matching row

            if user:
                # Store user information in the session
                session['user'] = {'username': user[0], 'email': user[1], 'phone': user[2], 'name': user[3], 'password': password}  # username = user[0], email = user[1], phone = user[2]
            
                # Now check if the user exists in the user_information table
                query_user_info = text('SELECT username FROM user_information WHERE username=:username')
                result_user_info = self.db.session.execute(query_user_info, {'username': username})
                user_info = result_user_info.fetchone()
                if not user_info:
                    # If user is not in user_information table, redirect to the quiz page
                    return redirect(url_for('quiz', name=session['user']['name'], username=session['user']['username'], phone=session['user']['phone'], email=session['user']['email']))
                else:
                    # If user exists in user_information table, redirect to the main page
                    return redirect(url_for('main'))  # Or your main dashboard page

            else:
                # If username or password is incorrect
                return render_template('login.html', message="Invalid username or password")

        # Render login page if the request method is GET
        return render_template('login.html', title='Fashion Hub')

    def signup(self):
     if request.method == 'POST':
         # Get user details from the signup form
         name = request.form['name']
         username = request.form['username']
         phone = request.form['phone']
         email = request.form['email']
         password = request.form['password']

         # Check if the username already exists in the login table
         query_check_username = text('SELECT username FROM login WHERE username=:username')
         result = self.db.session.execute(query_check_username, {'username': username})
         existing_user = result.fetchone()

         if existing_user:
             return render_template('signup.html', message="Username already exists. Please choose a different username.")

         # Store user details in the session for later use
         session['user_details'] = {
             'name': name,
             'username': username,
             'phone': phone,
             'email': email,
             'password': password
         }

         return render_template('quiz.html', name=session['user_details']['name'], username=session['user_details']['username'], phone=session['user_details']['phone'], email=session['user_details']['email'])
     return render_template('signup.html', title='Sign Up')


    def logout(self):
        # Clear the session data and log out the user
        session.pop('user', None)
        return redirect(url_for('main'))  # Redirect to the home page after logging out

class Profile:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.register_routes()

    def register_routes(self):
        self.app.add_url_rule('/profile', methods=['GET'], view_func=self.profile)
        self.app.add_url_rule('/quiz', methods=['GET', 'POST'], view_func=self.quiz)

    def profile(self):
        if 'user' in session:
            # Retrieve the username from session
            username = session['user']['username']
    
            # Query the user_information table for details based on the username
            result = db.session.execute(
                text("SELECT * FROM user_information WHERE username = :username"), 
                {"username": username}
            )
            user_info = result.fetchone()  # Fetch the first matching record
    
            if user_info:
                # Extracting data from the user_info tuple by index
                email = session['user']['email']
                phone = session['user'].get('phone', 'Not Provided')  # Default value if 'phone' is missing
                name = session['user']['name']
        
                # Assuming the columns are returned in this order:
                profile_pic = user_info[2]  # Update the index as per your table columns
                gender = user_info[3]
                date_of_birth = user_info[4]
                body_type = user_info[5]
                height = user_info[6]
                weight = user_info[7]
                preferred_color = user_info[8]
                preferred_fabrics = user_info[9]
                preferred_styles = user_info[10]
                occasion_types = user_info[11]
                style_goals = user_info[12]
                budget = user_info[13]
                skin_color = user_info[14]
                wardrobe_img = user_info[15]
        
                # Format date
                date_obj = datetime.strptime(str(date_of_birth), "%Y-%m-%d")
                f_date_of_birth = date_obj.strftime("%B %d, %Y")

                # Pass all data to the template
                return render_template(
                    'profile.html', 
                    username=username, 
                    email=email, 
                    phone=phone, 
                    name=name,
                    profile_pic=profile_pic,
                    gender=gender,
                    date_of_birth=f_date_of_birth,
                    body_type=body_type,
                    height=height,
                    weight=weight,
                    preferred_color=preferred_color,
                    preferred_fabrics=preferred_fabrics,
                    preferred_styles=preferred_styles,
                    occasion_types=occasion_types,
                    style_goals=style_goals,
                    budget=budget,
                    skin_color=skin_color,
                    wardrobe_img=wardrobe_img
                )
            else:
                # If no user info is found, redirect to login or show an error
                return redirect(url_for('login'))
        else:
            # If user is not logged in, redirect to login
            return redirect(url_for('login'))


    def quiz(self):
        if request.method == 'POST':
            # Get quiz data from the form
            profile_pic = request.form['profile_pic']
            gender = request.form['gender']
            date_of_birth = request.form['date_of_birth']
            body_type = request.form['body_type']
            height = request.form['height']
            weight = request.form['weight']
            preferred_color = request.form['preferred_color']
            preferred_fabrics = request.form['preferred_fabrics']
            preferred_styles = request.form['preferred_styles']
            occasion_types = request.form['occasion_types']
            style_goals = request.form['style_goals']
            budget = request.form['budget']
            skin_color = request.form['skin_color']
            wardrobe_img = request.form['wardrobe_img']

            # Ensure budget is a valid number (float)
            try:
                budget = float(budget)
            except ValueError:
                return render_template('quiz.html', title='Fashion Quiz', message="Please enter a valid number for the budget.")

            # Get user details from session
            user_details = session.get('user_details')
            print(session)
            print(user_details)
            if user_details:
                # Insert into login table
                insert_query_login = text('INSERT INTO login (name, username, phone, email, password) VALUES (:name, :username, :phone, :email, :password)')
                self.db.session.execute(insert_query_login, {
                    'name': user_details['name'],
                    'username': user_details['username'],
                    'phone': user_details['phone'],
                    'email': user_details['email'],
                    'password': user_details['password']
                })
                self.db.session.commit()

                # Insert into user_information table
                insert_query_info = text('''INSERT INTO user_information (username, profile_pic, gender, date_of_birth, body_type, height, weight, preferred_color, preferred_fabrics, preferred_styles, occasion_types, style_goals, budget, skin_color, wardrobe_img)
                                        VALUES (:username, :profile_pic, :gender, :date_of_birth, :body_type, :height, :weight, :preferred_color, :preferred_fabrics, :preferred_styles, :occasion_types, :style_goals, :budget, :skin_color, :wardrobe_img)''')
                self.db.session.execute(insert_query_info, {
                    'username': user_details['username'],
                    'profile_pic': profile_pic,
                    'gender': gender,
                    'date_of_birth': date_of_birth,
                    'body_type': body_type,
                    'height': height,
                    'weight': weight,
                    'preferred_color': preferred_color,
                    'preferred_fabrics': preferred_fabrics,
                    'preferred_styles': preferred_styles,
                    'occasion_types': occasion_types,
                    'style_goals': style_goals,
                    'budget': budget,  # Ensure this is a valid number
                    'skin_color': skin_color,
                    'wardrobe_img': wardrobe_img
                })
                self.db.session.commit()

                # Clear session data after the quiz
                session.pop('user_details', None)

                # Redirect to profile page after successful quiz
                return redirect(url_for('profile'))

            else:
                # If user details are missing from session, redirect to signup
                return redirect(url_for('login'))

        # If the request is GET, render the quiz page
        return render_template('quiz.html', title='Fashion Quiz')


# Initialize the classes
Dashboard(app)
Login(app, db)
Profile(app, db)

if __name__ == '__main__':
    app.secret_key = 'manojrajgopal15'  # Ensure you have a secret key for sessions
    app.run(debug=True)
