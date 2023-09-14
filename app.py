from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
import requests, random

config = {
    "DEBUG": True,
    "CACHE_TYPE": 'simple',
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.static_folder = 'static'
app.config.from_mapping(config)
cache = Cache(app)

JIKAN_BASE_URL = "https://api.jikan.moe/v4"

def index_anime(category, page):
    url = f"{JIKAN_BASE_URL}"
    params = {
        'page': page
    }
    if category == 'topani':
        url += '/top/anime?filter=airing&limit=10'
    elif category == 'seasonal':
        url += '/seasons/now?sfw'
    else:
        url += '/anime?&order_by=score&sort=desc&sfw&limit=10'
        params['genres'] = category

    # headers = {
    #     'Accept': 'application/json',
    #     'Content-Type': 'application/json'
    # }

    response = requests.get(url, params=params)
    results = response.json()
    return results


@app.route('/')
def index():
    current_page = request.args.get('page', default=1, type=int)
    seasonal_ani_data = index_anime('seasonal', current_page)

    total_pages = seasonal_ani_data['pagination']['last_visible_page']
    next_page = current_page + 1 if current_page < total_pages else total_pages
    prev_page = current_page - 1 if current_page > 1 else 1

    seasonal_ani = seasonal_ani_data['data']

    genres = [
        {'id': 1, 'name': 'Action'},
        {'id': 2, 'name': 'Adventure'},
        {'id': 4, 'name': 'Comedy'},
        {'id': 7, 'name': 'Mystery'},
        {'id': 8, 'name': 'Drama'},
        {'id': 10, 'name': 'Fantasy'},
        {'id': 14, 'name': 'Horror'},
        {'id': 18, 'name': 'Mecha'},
        {'id': 22, 'name': 'Romance'},
        {'id': 24, 'name': 'Sci-Fi'},
        {'id': 25, 'name': 'Shoujo'},
        {'id': 27, 'name': 'Shounen'},
        {'id': 30, 'name': 'Sports'},
        {'id': 36, 'name': 'Slice of Life'},
        {'id': 40, 'name': 'Psychological'},
        {'id': 42, 'name': 'Seinen'},
    ]

    random_genre = genres[random.randrange(0, len(genres))]
    top_genre = index_anime(random_genre['id'], 1)['data']

    @cache.cached(timeout=600)
    def cached_anime():
        url = f'{JIKAN_BASE_URL}/top/anime?filter=airing&sfw=&limit=10'
        response_cached = requests.get(url)
        result_cached = response_cached.json()
        return result_cached['data']

    top_ani = cached_anime()

    return render_template('layout.html', top_ani=top_ani, seasonal_ani=seasonal_ani,
                           total_pages=total_pages, next_page=next_page, prev_page=prev_page, current_page=current_page,
                           top_genre=top_genre, random_genre=random_genre)

@app.route('/load_more/<int:page>')
def load_more(page):
    url = f"{JIKAN_BASE_URL}/seasons/now?sfw&page={page}"
    response = requests.get(url)
    more_data = response.json()
    return jsonify(more_data['data'])

# @app.route('/livesearch', methods=['POST', 'GET'])
# def live_search():
#     if request.method == 'POST':
#         search_word = request.form['query']
#         print(search_word)
#         if len(search_word) > 0:
#             anime = search_anime(search_word, 5)
#         return jsonify({'htmlresponse': render_template('livesearch.html', anime=anime)})
#     # return render_template('layout.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            anime = search_anime(query)
            return render_template('results.html', anime=anime)
    return render_template('layout.html')


# will update to search filters
def search_anime(query):
    url = f"{JIKAN_BASE_URL}/anime?&order_by=score&sort=desc&sfw"
    params = {
        'q': query,
        # 'limit': limit,
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
