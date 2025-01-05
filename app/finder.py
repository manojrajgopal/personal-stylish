import requests
from dotenv import load_dotenv
import os
load_dotenv()

def search_google_api(query, api_key, cx, filters, num_results=30):
    search_url = "https://www.googleapis.com/customsearch/v1"
    query += " " + " ".join(filters)  # Add preferences to the query
    
    items = []
    for start_index in range(1, num_results + 1, 10):  # Fetch results in batches of 10
        params = {
            'q': query,
            'key': api_key,
            'cx': cx,
            'searchType': 'image',
            'num': 10,  # Google API allows up to 10 results per request
            'start': start_index
        }

        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get('items', []):
                title = item.get('title', 'Title not found')
                link = item.get('link', 'Link not found')
                snippet = item.get('snippet', 'Description not found')
                image = item.get('link', 'Image link not found')

                items.append({
                    'title': title,
                    'link': link,
                    'description': snippet,
                    'image': image
                })

        except requests.exceptions.RequestException as e:
            print("Error fetching data from Google API:", e)
            break

    return items

def display_results(items):
    if not items:
        print("No results found.")
        return

    for item in items:
        print(f"Title: {item['title']}")
        print(f"Description: {item['description']}")
        print(f"Image: {item['image']}")
        print("-" * 80)

def get_user_input():
    gender = input("Gender (e.g., Male, Female): ")
    age = input("Age (e.g., 25-30): ")
    body_type = input("Body Type (e.g., Slim, Athletic, Curvy): ")
    colors = input("Preferred Colors (comma separated): ").split(',')
    fabrics = input("Preferred Fabrics (comma separated): ").split(',')
    styles = input("Preferred Styles (comma separated): ").split(',')
    occasion_styles = input("Occasion Styles (comma separated): ").split(',')
    style_goals = input("Style Goals (comma separated): ").split(',')
    skin_color = input("Skin Color (e.g., Light, Dark, Olive): ")

    return [gender, age, body_type, *colors, *fabrics, *styles, *occasion_styles, *style_goals, skin_color]

if __name__ == "__main__":
    API_KEY = os.getenv('G_API_KEY')
    CX = os.getenv('G_CX')

    filters = get_user_input()
    user_input = input("Enter what you are looking for (e.g., winter fashion): ")

    results = search_google_api(user_input, API_KEY, CX, filters)
    display_results(results)
