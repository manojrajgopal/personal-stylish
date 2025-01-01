from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

class Main:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        self.app.add_url_rule('/', view_func=self.main, methods=['GET', 'POST'])

    def main(self):
        if request.method == "POST":
            # Handle form submission
            email = request.form.get("email")
            if email:
                print(f"New subscription: {email}")
        return render_template('index.html', title='Outfit Recommender')

class Login:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        self.app.add_url_rule('/login', view_func=self.login)

    def login(self):
        return render_template('login.html', title='Fashion Hub')  # Login Page

# Initialize the classes
Main(app)
Login(app)

if __name__ == '__main__':
    app.run(debug=True)
