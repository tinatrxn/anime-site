from flask import Flask, render_template, request, session
from flask_caching import Cache
from flask_session import Session
from ratelimit import limits, sleep_and_retry
from time import sleep
import requests, random, asyncio, aiohttp

from helpers import apology

config = {
    "DEBUG": True,
    "CACHE_TYPE": 'simple',
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.secret_key = "123qwe"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.static_folder = 'static'
app.config.from_mapping(config)
cache = Cache(app)

JIKAN_BASE_URL = "https://api.jikan.moe/v4"

search_genres = [
    {'id': 1, 'name': 'action'},
    {'id': 2, 'name': 'adventure'},
    {'id': 5, 'name': 'avant garde'},
    {'id': 46, 'name': 'award winning'},
    {'id': 4, 'name': 'comedy'},
    {'id': 8, 'name': 'drama'},
    {'id': 10, 'name': 'fantasy'},
    {'id': 47, 'name': 'gourmet'},
    {'id': 14, 'name': 'horror'},
    {'id': 7, 'name': 'mystery'},
    {'id': 22, 'name': 'romance'},
    {'id': 24, 'name': 'sci-fi'},
    {'id': 36, 'name': 'slice of life'},
    {'id': 30, 'name': 'sports'},
    {'id': 37, 'name': 'supernatural'},
    {'id': 41, 'name': 'suspense'}
]

search_themes = [
    {'id': 50, 'name': 'adult cast'},
    {'id': 51, 'name': 'anthropomorphic'},
    {'id': 53, 'name': 'childcare'},
    {'id': 54, 'name': 'combat sports'},
    {'id': 55, 'name': 'delinquents'},
    {'id': 39, 'name': 'detectives'},
    {'id': 56, 'name': 'educational'},
    {'id': 57, 'name': 'gag humor'},
    {'id': 58, 'name': 'gore'},
    {'id': 35, 'name': 'harem'},
    {'id': 59, 'name': 'high stake games'},
    {'id': 13, 'name': 'historical'},
    {'id': 60, 'name': 'idols (female)'},
    {'id': 61, 'name': 'idols (male)'},
    {'id': 62, 'name': 'isekai'},
    {'id': 63, 'name': 'iyashikei (healing/peaceful)'},
    {'id': 64, 'name': 'love polygon'},
    {'id': 66, 'name': 'magic girl shoujo'},
    {'id': 17, 'name': 'martial arts'},
    {'id': 18, 'name': 'mecha'},
    {'id': 67, 'name': 'medical'},
    {'id': 38, 'name': 'military'},
    {'id': 19, 'name': 'music'},
    {'id': 6, 'name': 'mythology'},
    {'id': 68, 'name': 'organized crime'},
    {'id': 69, 'name': 'otaku culture'},
    {'id': 20, 'name': 'parody'},
    {'id': 70, 'name': 'performing arts'},
    {'id': 71, 'name': 'pets'},
    {'id': 40, 'name': 'psychological'},
    {'id': 3, 'name': 'racing'},
    {'id': 72, 'name': 'reincarnation'},
    {'id': 73, 'name': 'reverse harem'},
    {'id': 74, 'name': 'romantic subtext'},
    {'id': 21, 'name': 'samurai'},
    {'id': 23, 'name': 'school'},
    {'id': 75, 'name': 'showbiz'},
    {'id': 29, 'name': 'space'},
    {'id': 11, 'name': 'strategy game'},
    {'id': 31, 'name': 'super power'},
    {'id': 76, 'name': 'survival'},
    {'id': 77, 'name': 'team sports'},
    {'id': 78, 'name': 'time travel'},
    {'id': 32, 'name': 'vampire'},
    {'id': 79, 'name': 'video game'},
    {'id': 80, 'name': 'visual arts'},
    {'id': 48, 'name': 'workplace'}
]

search_demographics = [
    {'id': 43, 'name': 'josei'},
    {'id': 15, 'name': 'kids'},
    {'id': 42, 'name': 'seinen'},
    {'id': 25, 'name': 'shoujo'},
    {'id': 27, 'name': 'shounen'}
]


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

    response = requests.get(url, params=params)
    results = response.json()
    return results


@app.route('/')
def index():
    session.pop('search', None)

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
                           search_genres=search_genres, search_themes=search_themes, search_demographics=search_demographics,
                           top_genre=top_genre, random_genre=random_genre)

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
    # user reached route via POST (submit a form via POST)
    params = None
    if request.method == 'POST':
        session.pop('search', None)

        query = request.form.get('query')
        search_type = request.form.get('type')
        min_score = request.form.get('min_score')
        status = request.form.get('status')
        rating = request.form.get('rating')
        genres_in = request.form.getlist('genre-include')
        genres_ex = request.form.getlist('genre-exclude')

        genres_include = ','.join(genres_in)
        genres_exclude = ','.join(genres_ex)


        filters = {
        'q': query,
        'type': search_type,
        'min_score': min_score,
        'status': status,
        'rating': rating,
        'genres': genres_include,
        'genres_exclude': genres_exclude
        }

        params = filter_check(filters)

        session['search'] = params

    # user reached route via GET

    # there should already be a session for search
    params = session['search']
    current_page = request.args.get('page', default=1, type=int)
    sort = request.args.get('sort', default='desc', type=str)
    order_by = request.args.get('order_by', default='score', type=str)

    params['order_by'] = order_by
    params['sort'] = sort
    session['search'] = params

    orders = {
        'score': 'Score',
        'rank': 'Rank',
        'popularity': 'Popularity',
        'members': '# of Members',
    }

    if params:
        search_data = search_anime(params, current_page)

        total_pages = search_data['pagination']['last_visible_page']
        next_page = current_page + 1 if current_page < total_pages else total_pages
        prev_page = current_page - 1 if current_page > 1 else 1

        anime_results = search_data['data']

        return render_template('results.html', anime_results=anime_results, params=params, order_by=order_by, orders=orders, sort=sort,
                                search_genres=search_genres, search_themes=search_themes, search_demographics=search_demographics,
                                current_page=current_page, next_page=next_page, prev_page=prev_page, total_pages=total_pages)

    # user reached route via GET (as by clicking a link or via redirect)
    return apology(f"search isn't working, {session['search']}", 400)


# changes genres list into string
# def list_to_string(list):
#     if

# compares dicts - outputs correct params
def filter_check(dict):
    params = {
        'q': None,
        'type': None,
        'min_score': None,
        'status': None,
        'rating': None,
        'genres': None,
        'genres_exclude': None
    }

    for k in list(dict.keys()):
        if dict[k] == "":
            del params[k]
        elif dict[k] != None:
            params[k] = dict[k]
        else:
            del params[k]

    return params

# will update to search filters
def search_anime(params, page):
    url = f"{JIKAN_BASE_URL}/anime?sort=desc&sfw"
    params1 = params
    params1['page'] = page
    response = requests.get(url, params=params)
    results = response.json()
    return results


@app.route('/<int:animeid>')
@cache.cached(timeout=600)
async def details(animeid):

    anime_details = []
    detail_url = f"{JIKAN_BASE_URL}/anime/{animeid}"
    urls = [f"{detail_url}/full", f"{detail_url}/episodes", f"{detail_url}/recommendations"]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            check_limit1()
            check_limit2()
            check_limit3()

            response = await session.get(url, ssl=False)
            result = await response.json()
            anime_details.append(result)

    pre_details = anime_details[0]['data']
    details = await empty_details(pre_details)

    episodes = anime_details[1]
    latest_episode = None

    if episodes['pagination']['has_next_page'] == True:
        async with aiohttp.ClientSession() as session:
            check_limit1()
            check_limit3()

            last_page = episodes['pagination']['last_visible_page']
            response = await session.get(f"{detail_url}/episodes?page={last_page}", ssl=False)
            result = await response.json()
            episodes_data = result['data'][-1]
            latest_episode = episodes_data['mal_id']
    elif not episodes['data']:
        latest_episode = 0
    else:
        episodes_data = episodes['data'][-1]
        latest_episode = episodes_data['mal_id']

    recommendations = anime_details[2]['data']

    return render_template('anime-page.html', details=details, episodes=episodes, latest_episode=latest_episode, recommendations=recommendations,
                           search_genres=search_genres, search_themes=search_themes, search_demographics=search_demographics)


async def empty_details(details):
    detail = ['type', 'studios', 'rating', 'score', 'rank', 'studios', 'relations', 'images', 'demographics']

    for item in detail:
        # if item is nulll
        if not details[item]:
            details[item] = '¯_(ツ)_/¯'

    return details

@sleep_and_retry
@limits(calls=2, period=1)
def check_limit1():

    return

@sleep_and_retry
@limits(calls=2, period=1)
def check_limit2():
    sleep(0.3)
    return

@sleep_and_retry
@limits(calls=60, period=60)
def check_limit3():

    return

if __name__ == "__main__":
    app.run(debug=True)
