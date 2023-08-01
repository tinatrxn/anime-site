from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

JIKAN_BASE_URL = "https://api.jikan.moe/v4"

@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            anime = search_anime(query)
            return render_template('results.html', anime=anime)
    return render_template('layout.html')

def search_anime(query):
    url = f"{JIKAN_BASE_URL}/anime?type=tv&order_by=score&sort=desc&sfw"
    params = {
        'q': query,
        'page': 1,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, params=params, headers=headers)
    results = response.json()
    return results['data'] if 'data' in results else []




if __name__ == "__main__":
    app.run(debug=True)
