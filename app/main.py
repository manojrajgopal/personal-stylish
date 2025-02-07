from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, date
from werkzeug.utils import secure_filename
from app.finder import FashionFinder
from app.database import DatabaseInitializer
from ai_engine.fashion_recommender import recommend_fashion
from ai_engine.age_gender_skinTone import process_fashion_recommendation
#from celery_setup import celery
import pymysql
import os
import google.generativeai as ai
import logging
import atexit
import time

# Directory to save the images
PROFILE_PIC_FOLDER = 'app/static/uploads/profile/'
WARDROBE_IMG_FOLDER = 'app/static/uploads/wardrobe/'

os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)
os.makedirs(WARDROBE_IMG_FOLDER, exist_ok=True)

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"
logging.getLogger('google.generativeai').setLevel(logging.CRITICAL)
logging.getLogger('grpc').setLevel(logging.CRITICAL)

API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY is None:
    raise ValueError("API_KEY environment variable is not set!")

ai.configure(api_key=API_KEY)

# Create a new model
model = ai.GenerativeModel("gemini-pro")
chat = model.start_chat()

pymysql.install_as_MySQLdb()  # This will make PyMySQL work as MySQLdb

app = Flask(__name__)
app.config['SECRET_KEY'] = 'manoj_rajgopal_1509'

# Configuring the database connection
db_initializer = DatabaseInitializer()
db_initializer.initialize_database()

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
            username = request.form['username'].lower()
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
         name = request.form['name'].title()
         username = request.form['username'].lower().strip().replace(" ", "")
         phone = request.form['phone']
         email = request.form['email'].lower()
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
                user_title = user_info[16]
                user_about_1 = user_info[17]
                user_about_2 = user_info[18]

                current_date = datetime.now().date()

                if date_of_birth:
                    age = current_date.year - date_of_birth.year - ((current_date.month, current_date.day) < (date_of_birth.month, date_of_birth.day))
                    # Categorize based on age
                    if age < 18:
                        if gender.lower() == "male":
                            gender = "Boys"
                        elif gender.lower() == "female":
                            gender = "Girls"
                        else:
                            gender = "Other"
                    else:
                        if gender.lower() == "male":
                            gender = "Men"
                        elif gender.lower() == "female":
                            gender = "Women"
                else:
                    age = 0
                    gender = "Unisex"
                        
                category_dict = recommend_fashion(
                                    gender=gender,
                                    baseColour=[color.strip() for color in (preferred_color or "").split(',')],
                                    preferredFabrics=[fabrics.strip() for fabrics in (preferred_fabrics or "").split(',')],
                                    preferredStyles=[styles.strip() for styles in (preferred_styles or "").split(',')],
                                    occasionTypes=[occasion.strip() for occasion in (occasion_types or "").split(',')],
                                    styleGoals=[goal.strip() for goal in (style_goals or "").split(',')],
                                    bodyType=body_type
                                )

                
                # Format date
                if date_of_birth:
                    date_obj = datetime.strptime(str(date_of_birth), "%Y-%m-%d")
                    f_date_of_birth = date_obj.strftime("%B %d, %Y")
                else:
                    # Handle the case where date_of_birth is None
                    f_date_of_birth = "Unknown"  # Or use a default value like "January 01, 2000"

                if gender.lower() == 'boys':
                    profile_image = 'avatar-1.png'
                elif gender.lower() == 'girls':
                    profile_image = 'avatar-2.png'
                elif gender.lower() == 'men':
                    profile_image = 'male-avatar.png'
                elif gender.lower() == 'women':
                    profile_image = 'avatar-3.png'
                else:
                    profile_image = 'avatar-4.png'

                
                
                # Fetch trove data based on the filters

                # Pass all data to the template
                return render_template(
                    'profile.html', 
                    profile_image=profile_image,
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
                    wardrobe_img=wardrobe_img,
                    one_word_user=user_title,
                    paragraph_1=user_about_1,
                    paragraph_2=user_about_2,
                    category_dict=category_dict
                )
            else:
                # If no user info is found, redirect to login or show an error
                return redirect(url_for('login'))
        else:
            # If user is not logged in, redirect to login
            return redirect(url_for('login'))

    def quiz(self):
        profile_pic_filename = None
        wardrobe_img_filename = None
        date_of_birth = None
        user_title = None
        user_about_1 = "No title available"  # Default value
        user_about_2 = "No description available"  # Default value
        gender = 'Other' # Default value
        body_type = None # Default value
        skin_color = None

        if request.method == 'POST':
            # Get quiz data from the form
            profile_pic = request.files.get('profile_pic')
            gender = request.form.get('gender') or None
            date_of_birth_str = request.form['date_of_birth'] or None
            body_type = request.form.get('body_type') or None
            height = request.form['height'] or None
            weight = request.form['weight'] or None
            preferred_color = request.form['preferred_color'] or None
            preferred_fabrics = request.form['preferred_fabrics'] or None
            preferred_styles = request.form['preferred_styles'] or None
            occasion_types = request.form['occasion_types'] or None
            style_goals = request.form['style_goals'] or None
            budget = request.form['budget'] or 0
            skin_color = request.form.get('skin_color') or None
            wardrobe_img = request.files.get('wardrobe_img')
        
            print("Form Data:", request.form)
            print("Files:", request.files)

            if date_of_birth_str:
                try:
                    date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()  # Convert to date format
                    current_date = date.today()
                    age = current_date.year - date_of_birth.year - ((current_date.month, current_date.day) < (date_of_birth.month, date_of_birth.day))
                except ValueError:
                    return render_template('quiz.html', title='Fashion Quiz', message="Invalid date format. Please enter a valid date.")

            # Ensure age-based gender adjustment only runs if date_of_birth is valid
            if gender == 'Male' and date_of_birth:
                gender = 'Boys' if age < 18 else 'Men'
            elif gender == 'Female' and date_of_birth:
                gender = 'Girls' if age < 18 else 'Women'


            user_details = session.get('user_details')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            
            if wardrobe_img:
                wardrobe_img_filename = f"{user_details['username']}_{timestamp}_{secure_filename(wardrobe_img.filename)}"
                wardrobe_img_path = os.path.join(WARDROBE_IMG_FOLDER, wardrobe_img_filename)
                wardrobe_img.save(wardrobe_img_path)

            if profile_pic:
                profile_pic_filename = f"{user_details['username']}_{timestamp}_{secure_filename(profile_pic.filename)}"

                profile_pic_path = os.path.join(PROFILE_PIC_FOLDER, profile_pic_filename)

                profile_pic.save(profile_pic_path)

                detected_tone_hex, recommended_colors, gender_category, detected_age, outfits = process_fashion_recommendation(profile_pic_path)
                
                print("****************************************************************")
                print(detected_tone_hex, recommended_colors, gender_category, detected_age, outfits)

            if user_details['name'] and gender and date_of_birth_str and body_type and height and weight and preferred_color and preferred_fabrics and preferred_styles and occasion_types and style_goals and skin_color:
                prompt = f"""
                    Generate a professionally written, engaging, and personalized "About" section for a user profile in two short paragraphs (90-105 words in total). The content should impress the reader and reflect the user's unique style and preferences. Use the following details:
                    - Name: {user_details['name']}
                    - Gender: {gender}  
                    - Age: {date_of_birth_str}  
                    - Body Type: {body_type}  
                    - Height: {height}  
                    - Weight: {weight}  
                    - Preferred Colors: {preferred_color}  
                    - Preferred Fabrics: {preferred_fabrics}  
                    - Preferred Styles: {preferred_styles}  
                    - Occasion Types: {occasion_types}  
                    - Style Goals: {style_goals}  
                    - Skin Color: {skin_color}

                    Ensure the language is elegant, concise, and makes the user sound fashion-forward and confident. Avoid repetition and use positive, inspiring vocabulary.
                    """
            
                response = chat. send_message (prompt)
                paragraph = response.text
                paragraph = paragraph.split("\n\n")
                user_about_1 = paragraph[0]
                user_about_2 = paragraph[1]
            
                prompt = f"""
                    Using the following details about a user, provide one word that best describes the overall style or impression of the individual. Focus solely on the most fitting adjective or noun that reflects the user's fashion preferences, style goals, and persona. Do not add any special characters like asterisks or quotation marks—just return the word itself.

                    Details:
                    - Name: {user_details['name']}
                    - Gender: {gender}
                    - Age: {date_of_birth}
                    - Body Type: {body_type}
                    - Height: {height}
                    - Weight: {weight}
                    - Preferred Colors: {preferred_color}
                    - Preferred Fabrics: {preferred_fabrics}
                    - Preferred Styles: {preferred_styles}
                    - Occasion Types: {occasion_types}
                    - Style Goals: {style_goals}
                    - Skin Color: {skin_color}
                    """

                response = chat.send_message(prompt)
                clean_output = response.text.strip().replace('*', '')  # Removing any asterisks
                user_title = clean_output
                # Ensure budget is a valid number (float)
            try:
                budget = float(budget) if budget else None
            except ValueError:
                return render_template('quiz.html', title='Fashion Quiz', message="Please enter a valid number for the budget.")

            # Get user details from session
            user_details = session.get('user_details', {})
            if not user_details:
                return redirect(url_for('login'))  # Redirect if session data is missing


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
                insert_query_info = text('''INSERT INTO user_information (username, profile_pic, gender, date_of_birth, body_type, height, weight, preferred_color, preferred_fabrics, preferred_styles, occasion_types, style_goals, budget, skin_color, wardrobe_img, user_title, user_about_1, user_about_2)
                                        VALUES (:username, :profile_pic, :gender, :date_of_birth, :body_type, :height, :weight, :preferred_color, :preferred_fabrics, :preferred_styles, :occasion_types, :style_goals, :budget, :skin_color, :wardrobe_img, :user_title, :user_about_1, :user_about_2)''')
                self.db.session.execute(insert_query_info, {
                    'username': user_details['username'],
                    'profile_pic': profile_pic_filename or None,
                    'gender': gender or None,
                    'date_of_birth': date_of_birth or None,
                    'body_type': body_type or None,
                    'height': height or None,
                    'weight': weight or None,
                    'preferred_color': preferred_color or None,
                    'preferred_fabrics': preferred_fabrics or None,
                    'preferred_styles': preferred_styles or None,
                    'occasion_types': occasion_types or None,
                    'style_goals': style_goals or None,
                    'budget': budget or None,  # Ensure this is a valid number
                    'skin_color': skin_color,
                    'wardrobe_img': wardrobe_img_filename or None,
                    'user_title': user_title or None,
                    'user_about_1': user_about_1 or None,
                    'user_about_2': user_about_2 or None,
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

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set limit to 16MB

# Initialize the classes
Dashboard(app)
Login(app, db)
Profile(app, db)

if __name__ == '__main__':
    app.secret_key = 'manojrajgopal15'  # Ensure you have a secret key for sessions
    app.run(debug=True)