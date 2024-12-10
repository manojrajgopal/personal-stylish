from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('index.html', title='Outfit Recommender')  # Flask looks in 'templates' by default

if __name__ == '__main__':
    app.run(debug=True)
