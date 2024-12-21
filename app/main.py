from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == "POST":
        # Handle form submission
        email = request.form.get("email")
        if email:
            print(f"New subscription: {email}")
    return render_template('index.html', title='Outfit Recommender')  # Flask looks in 'templates' by default


if __name__ == '__main__':
    app.run(debug=True)
