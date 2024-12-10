from flask import Flask
import requests

app = Flask(__name__)
@app.route('/')
def hello_world():
    api_key = "78542c411a2b9031ae9cb9bef906dc2f"
    city = "Bengaluru"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"

    response = requests.get(url)
    data = response.json()

    return str(data['main']['temp'] - 273.15)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
