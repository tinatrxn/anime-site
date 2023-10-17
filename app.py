from flask import Flask, render_template, request, session
from flask_caching import Cache
from flask_session import Session
from ratelimit import limits, sleep_and_retry
from time import sleep
import requests, random, asyncio, aiohttp


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

ALL_GENRES = [
    {'id': 1, 'name': 'action', 'description': "Exciting action sequences take priority and significant conflicts between characters are usually resolved with one's physical power. While the overarching plot may involve one group against another, the narrative in action stories is always focused on the strengths/weaknesses of individual characters and the effort they put into their personal battles with the opposing group's members. Contrast with Military or Sports where the narrative is on collective achievement, or monster-of-the-week where the brief action scenes are a predicted climax to the episode's plot."},
    {'id': 2, 'name': 'adventure', 'description': "Whether aiming for a specific goal or just struggling to survive, the main character is thrust into unfamiliar situations or lands and continuously faces unexpected dangers. The narrative of adventure stories is always on how the characters react to sudden events or trials during the journey, indicating personal growth or setback based on which actions or choices are taken. Character development as a response to the journey's dangers is a requirement of adventure stories. Simply experiencing foreign lands or worlds is not adventure."},
    {'id': 5, 'name': 'avant garde', 'description': "Experimental fiction which shunned conventional storytelling at the time it was created. These stories often invoke unsettled feelings because they reject traditional ways in which we prefer to view (or escape from) the world. Narrative is avant garde works is often of higher importance than the content. Deconstructions often fall into this genre. Note that simply being darker, edgier, or cynical doesn't mean the work is avant garde."},
    {'id': 46, 'name': 'award winning', 'description': "Titles which have won prestigious or professional awards in Japan. Examples include the Tokyo Anime Award or Japan Media Arts Festival awards."},
    {'id': 4, 'name': 'comedy', 'description': "Uplifting the audience with positive emotion takes priority, eliciting laughter, amusement, or general entertainment. Almost always, comedy stories are episodic or have happy endings. Nearly every work will use comedy as a plot device to relieve tension, but the overarching narrative must be focused on evoking amusement to be Comedy. Drama and Comedy are not mutually exclusive, but mixing them requires the audience facing human struggle with lightheartedness. Slice of Life and Comedy are incompatible by definition."},
    {'id': 8, 'name': 'drama', 'description': "Plot-driven stories focused on realistic characters experiencing human struggle. Because drama stories ask the question of what it means to be human, the conflict and emotions will be relatable, even if the settings or characters themselves are not. Here, you will see humanity at its worst, its best, and everything in between. Simply having a serious tone, dramatic moments, or evoking tears does not equal Drama. If the narrative focuses on eliciting emotional reactions rather than on characterization, then it is melodrama and not Drama. Slice of Life and Drama are incompatible by definition."},
    {'id': 10, 'name': 'fantasy', 'description': "Magical powers, unnatural creatures, or other unreal elements which cannot be explained by science are prevalent and normal to the setting they exist in. Fantasy stories can take place on Earth (urban fantasy) or in another world. Character traits (e.g. magician vs demon/spirit) and setting do not determine if a story is Fantasy. If majority of the cast has magical or supernatural powers (e.g. one normal highschool boy surrounded by five goddesses), then the story is Fantasy. If only a few characters have powers and most of the cast would be in disbelief to discover this (e.g. one man is an exorcist and the rest are normal adults), then the story is Supernatural. Sometimes a story can be both Fantasy and Supernatural, but this is rare."},
    {'id': 47, 'name': 'gourmet', 'description': "Preparation and consumption of food or drink take focus in gourmet stories and the narrative is designed to feature numerous different dishes or beverages. Characters are often chefs or food connoisseurs, and special attention is given to all steps in the cooking process, ranging from detailed descriptions of recipes to the characters' often over-the-top reactions when tasting the finished product. Gourmet should only be double-tagged with Workplace when the social interactions between multiple employees in the same work environment are equal in focus to the food/drink."},
    {'id': 14, 'name': 'horror', 'description': "Creating—and maintaining—a sense of dread in the audience takes priority, eliciting shock, fear, or disgust through atmosphere and frightening scenarios. Mood must be of equal or greater importance than setting and characterization in horror stories. Almost always, the main cast will be under constant threat of danger. Many stories can incorporate elements of horror as a plot device to unnerve the audience, but the overarching narrative must be focused on evoking and maintaining apprehension to be Horror. Contrast with Suspense where the audience craves to know what will happen next rather than fearing it."},
    {'id': 7, 'name': 'mystery', 'description': "Whether its solving a crime or finding an explanation for a puzzling circumstance, the main cast willingly or reluctantly become investigators who must work to answer the who, what, why, and/or how of the current dilemma. The narrative of mystery stories is always on collecting evidence, identifying suspects, and theorizing possible scenarios for the unexplainable, before finally capturing the perpetrator or resolving the current situation. Almost always, the audience has the same information as the main characters and anticipation is directed towards discovering the explanation, not what will transpire after the answer is found. Contrast with Suspense or Horror where often the audience has more information than the cast, which heightens the tension or fear of what will happen next."},
    {'id': 22, 'name': 'romance', 'description': "Falling in love and struggling to progress towards—or maintain—a romantic relationship take priority, while other subplots either take backseat or are designed to develop the main love story. The narrative focuses on the thoughts and emotions of the characters, illustrating the connections between them and explaining their reactions to events or conflict. Almost always, the story ends happily and the couple is rewarded for their efforts with lasting love. Romance stories require significant romantic development leading to some kind of conclusion: either to begin the relationship, continue it, or end it. Open-ended romantic endings are only acceptable when the work is an incomplete adaptation of a Romance source. 'Teasing' stories which do not narrate significant romantic development but have a conclusion should be tagged Romantic Subplot. A story can be simply Romance. Since they are plot-driven stories showing humans experiencing romantic struggle, most Romance has some Drama inherently. For both tags, the drama should be focused not only on the relationship but also on the side storylines; for example, one character overcoming the death of a loved one or a drug addiction. Comedy requires Romance narratives to be focused on eliciting laughter, not only using comedy for lightheartedness. Slice of Life and Romance are incompatible by definition."},
    {'id': 24, 'name': 'sci-fi', 'description': "Imagined technological advancements or natural settings which are currently unreal in the present day but could be invented, caused, or explained by science in the future. The narrative of science fiction (Sci-Fi or SF) stories focuses on the societal or individual reprecussions caused by the imagined technology or natural phenomenon, and are frequently dystopian in nature. Sufficient world-building is required for a work to be Sci-Fi; an alien simply visiting from outer space and living on Earth with unusual powers would be Supernatural. Characters in Sci-Fi stories can have unnatural powers without a Fantasy/Supernatural tag, but there should be a plausible scientific reason for these powers described by the creator. A futuristic setting with impossible, unexplained powers (e.g. humans randomly evolved to control the weather via thought) would be Fantasy."},
    {'id': 36, 'name': 'slice of life', 'description': "Slice of Life stories are focused on a seemingly random and mundane period of the main characters' lives. The absence of a central plot to carry the story towards a charted destination means Slice of Life stories frequently lack overarching conflict and resolution. While life is not without conflict and Slice of Life neither, here conflict appears and dissipates seemingly at will, without a specific narrative to enforce it. Slow story pacing or episodic storytelling does not equal Slice of Life. Drama/Romance stories can be slow and soft while maintaining a central plot of human/relationship struggle. Comedy stories may lack progress and have mundane settings, but they have narratives focused on eliciting laughter rather than amusing moments happening naturally. Thus, Slice of Life is incompatible with Comedy, Drama, and Romance by definition."},
    {'id': 30, 'name': 'sports', 'description': "Training for and participating in a sport take priority, with the goal of furthering one's athletic abilities—either to win a competition or achieve some social standing. While the featured sport may be individual or team, the main cast will always overcome conflict through discussion and insights gained from other athletes or coaches. This creates a general sense of collective support and achievement that is always present in Sports stories. Contrast with Action where the narrative is on resolving conflict with one's physical power. While both Action and Sports may focus on exciting action sequencies, the two genres are mutually exclusive."},
    {'id': 37, 'name': 'supernatural', 'description': "Primarily taking place on Earth, supernatural stories incorporate elements or attributes that are unnatural and unexplainable by science. Creatures common in folklore (ghosts, vampires) or humans with metaphysical powers (telekinesis, mind reading) are often featured. Character traits (e.g. demon/spirit) and setting alone do not determine if a story is Supernatural. If only a few characters have powers and most of the cast would be in disbelief to discover this (e.g. one man is an exorcist and the rest are normal adults), then the story is Supernatural. If majority of the cast has magical or supernatural powers (e.g. one normal highschool boy surrounded by five goddesses), then the story is Fantasy. Sometimes a story can be both Supernatural and Fantasy, but this is rare."},
    {'id': 41, 'name': 'suspense', 'description': "Instilling a sense of anticipation and excitement takes priority, and is accomplished with a narrative that is rife with twists, turns, and red herrings. Uncertainty is present every step of the way, often drawn out for maximum effect. A variety of tools are used to keep the audience on the edge of their seats, such as withholding important information, intentional misdirection, or even outright subversion of expectations. Suspenseful moments do not mean a work is Suspense; the feeling of anticipation or anxiety must be maintained throughout the story. Contrast with Horror where the audience is in a constant state of apprehension and dreads the next event, rather than craving it. While Mystery also instills anticipation, the tension is focused on discovering the solution to a puzzle, rather than knowing what the characters will do next. Sometimes a story can mix Suspense with Horror or Mystery, but this is rare."},
    {'id': 50, 'name': 'adult cast', 'description': "As many animes are focussed on characters in high school or younger, it's refreshing to have series where they focus on the lives of adults."},
    {'id': 51, 'name': 'anthropomorphic', 'description': "Animals with human characteristics."},
    {'id': 53, 'name': 'childcare', 'description': "Raising children in all kinds of environments."},
    {'id': 54, 'name': 'combat sports', 'description': "Individual sports which involve one-on-one physical confrontations. This theme includes sports such as boxing, wrestling, karate, judo etc. Since Combat Sports is a theme within the Sports genre, these stories must have matches held in a competitive or organized setting."},
    {'id': 55, 'name': 'delinquents', 'description': "Troubled kids facing the consequences of their actions."},
    {'id': 39, 'name': 'detectives', 'description': "A theme within the Mystery genre, these stories feature either a detective or amateur investigator working to solve a crime or puzzling event. To classify as Detective, the character must either by employed as an investigator (e.g. police officer, private detective) or be sought out by enforcement/clients because of their case-solving reputation (e.g. Sherlock). If the character only seeks out mysteries as a hobby or becomes embroiled in them randomly, then the Detective theme does not apply. Anti-heroes being pursued by enforcement is not Detective."},
    {'id': 56, 'name': 'educational', 'description': "Learning real subjects while enjoying anime."},
    {'id': 57, 'name': 'gag humor', 'description': "Quick punchlines and just silly non-sense."},
    {'id': 58, 'name': 'gore', 'description': "For those who don't have a weak stomach. Lots of violence, bloodshed, and more."},
    {'id': 35, 'name': 'harem', 'description': "Polygynous relationships; a man with a number of partners."},
    {'id': 59, 'name': 'high stake games', 'description': "Risky moves that most likely end with death."},
    {'id': 13, 'name': 'historical', 'description': "Mostly focussing on Japanese or English history."},
    {'id': 60, 'name': 'idols (female)', 'description': "Looking at the lives of female Japanese pop idols."},
    {'id': 61, 'name': 'idols (male)', 'description': "Looking at the lives of male Japanese pop idols."},
    {'id': 62, 'name': 'isekai', 'description': "A widely popular theme in Japan in which a character is suddenly transported from their world into a new/unfamiliar one."},
    {'id': 63, 'name': 'iyashikei (healing/peaceful)', 'description': "The Japanese word 'iyashi' (癒し) means healing, and the term 'iyashikei' refers to anime and manga that 'heal' the audience by instilling a calming feeling or evoking emotional catharsis. Almost always, Iyashikei stories have peaceful, somewhat mundane, and nostalgic atmospheres. The settings are idyllic with little or no conflict, and the narratives focus on personal reflection, heartwarming moments, a vague sense of melancholy, and/or an appreciation for the small things in life. Iyashikei is a theme within the Slice of Life genre, and thus the conditions for both defintions must be met for the tag. Pets-themed stories are a subcategory of Iyashikei, so they are not double-tagged."},
    {'id': 64, 'name': 'love polygon', 'description': "When one characer has more than 1 person trying to pursue them."},
    {'id': 66, 'name': 'magic girl shoujo', 'description': "Strong girls with magical powers!"},
    {'id': 17, 'name': 'martial arts', 'description': "All different kinds of fighting."},
    {'id': 18, 'name': 'mecha', 'description': "Big fighting machines, usually paired with some sort of war."},
    {'id': 67, 'name': 'medical', 'description': "Doctors and other healthcare professionals."},
    {'id': 38, 'name': 'military', 'description': "Government militaries, wars, and fighting."},
    {'id': 19, 'name': 'music', 'description': "Ranges from classical, to rock, to idols, and even to school bands."},
    {'id': 6, 'name': 'mythology', 'description': "Stories pertaining to their own myths or based on cultural or religious myths."},
    {'id': 68, 'name': 'organized crime', 'description': "Groups of individuals that pull off illegal plans."},
    {'id': 69, 'name': 'otaku culture', 'description': "Otaku is a term in used in modern Japan to refer to people with obsessive interests. Outside of Japan, it specifically denotes people who have a heavy interest in anime, manga, and other Japanese culture or entertainment. Otaku Culture themed stories have a plot which is related to the hobbies or occupation of a main cast who are heavily involved in anime-related media. Characters could be creating anime or manga (professionally or casually with friends), attending conventions or idol concerts, dressing up in cosplay, etc."},
    {'id': 20, 'name': 'parody', 'description': "Imitating the styles of other media with deliberate exaggeration for comic effect."},
    {'id': 70, 'name': 'performing arts', 'description': "The main cast of these stories practice and perform live while using their body movements and/or voice as a form of artistic expression. Performing Arts are meant to capture attention with artistic beauty and deliver an unspoken message which evokes emotion in the audience. Often, characters will discuss the meanings behind classical sequences by renowned creators, or will strive to create their own. Primary examples of Performing Arts are dance, theater, and opera, but the theme also includes other forms of artistic expression such as choreographed circus sequences, folk music, or rakugo. Popular contemporary music (e.g. idols, rock bands) is not included in Performing Arts."},
    {'id': 71, 'name': 'pets', 'description': "Humans and their little best friend, or just about the best friend."},
    {'id': 40, 'name': 'psychological', 'description': "Emphasizing interior characterization and motivation to explore the spiritual, emotional, and mental lives of characters."},
    {'id': 3, 'name': 'racing', 'description': "Vroom vroom skrrrrrr."},
    {'id': 72, 'name': 'reincarnation', 'description': "After death, a new life and world is approaching you."},
    {'id': 73, 'name': 'reverse harem', 'description': "Polyandrous relationships; a woman with a number of partners."},
    {'id': 74, 'name': 'romantic subtext', 'description': "Romantic Subtext is a narrative which can at first appear to be Romance. These plots feature one or more main couples which seem to have romantic interest in each other, and whose relationship(s) will be central to the main story. However, while the story will set the couple up for heartwarming or embarrassing moments, these encounters will not lead to any significant romantic development, and the characters will not strive to deepen the relationship beyond a certain boundary. Some early indicators of Romantic Subtext include a missing emotional throughline (lack of personal reflection which allows the characters to understand their feelings and share these with the audience) and a lack of any conflict which will deepen or drive the relationship apart. Almost always, Romantic Subtext is a theme under the Comedy genre and these stories have plots designed to uplift the audience with positive emotion or amusement."},
    {'id': 21, 'name': 'samurai', 'description': "Historical Japanese warriors."},
    {'id': 23, 'name': 'school', 'description': "Main story setting is in school."},
    {'id': 75, 'name': 'showbiz', 'description': "Show business, or Showbiz for short, describes the industry which produces popular entertainment media such as television shows, movies, radio programs, magazines, and mainstream contemporary music. One or main characters in Showbiz themed stories work in the entertainment industry, either as a performer (e.g. actress, model) or in business development (e.g. manager, producer). Their occupation should also be central to the main story's plotline. For example, simply dating a famous band member but never seeing that character perform or struggle with their profession is not Showbiz."},
    {'id': 29, 'name': 'space', 'description': "Many different stories of what else could be out here."},
    {'id': 11, 'name': 'strategy game', 'description': "Sometimes about real strategy board games, but most are made-up fantasy games."},
    {'id': 31, 'name': 'super power', 'description': "Humans with a wide variety of different powers."},
    {'id': 76, 'name': 'survival', 'description': "When characters don't know if they will be alive for another day."},
    {'id': 77, 'name': 'team sports', 'description': "Sports which require multiple athletes on one team to compete against multiple athletes on another team, within same playing field and at the same time. Team Sports narratives focus on improving one team's collective performance, and frequently require its members to deepen their relationships with each other in order to bring out each member's strengths. This theme includes many ball games such as baseball, volleyball, basketball, rugby, hockey, etc."},
    {'id': 78, 'name': 'time travel', 'description': "Characters moving to different times."},
    {'id': 32, 'name': 'vampire', 'description': "Your non-traditional creepy pale vampires."},
    {'id': 79, 'name': 'video game', 'description': "Gaming meets anime."},
    {'id': 80, 'name': 'visual arts', 'description': "The main cast of these stories practice and create physical objects for visual perception using tools and established art forms. Characters will study established techniques and/or strive to create new pieces of art work for designated projects or to sell professionally. Visual Arts includes artistic methods such as drawing, painting, photography, sculpture, ceramics, calligraphy, etc. Popular contemporary art forms (e.g. manga, anime) are not included in Visual Arts."},
    {'id': 48, 'name': 'workplace', 'description': "Because work can be fun too."},
    {'id': 43, 'name': 'josei', 'description': "Audience Demographic: Older women or teenagers."},
    {'id': 15, 'name': 'kids', 'description': "Audience Demographic: Children."},
    {'id': 42, 'name': 'seinen', 'description': "Audience Demographic: Young adult men."},
    {'id': 25, 'name': 'shoujo', 'description': "Audience Demographic: Adolescent girls or young adult women."},
    {'id': 27, 'name': 'shounen', 'description': "Audience Demographic: Adolescent boys or young adult men."}
]

ORDERS = {
    'score': 'Score',
    'popularity': 'Popularity'
}

@app.route('/')
async def index():
    current_page = request.args.get('page', default=1, type=int)
    seasonal_ani_data = index_anime('seasonal', current_page)

    pages = await pagination(seasonal_ani_data, current_page)
    total_pages = pages['total_pages']
    next_page = pages['next_page']
    prev_page = pages['prev_page']

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
                           all_genres=ALL_GENRES, top_genre=top_genre, random_genre=random_genre)


def index_anime(category, page):
    url = f"{JIKAN_BASE_URL}"
    params = {
        'page': page
    }
    if category == 'seasonal':
        url += '/seasons/now?sfw'
    else:
        url += '/anime?&order_by=score&sort=desc&sfw&limit=10'
        params['genres'] = category

    response = requests.get(url, params=params)
    results = response.json()
    return results

async def pagination(ani_data, current_page):
    total_pages = ani_data['pagination']['last_visible_page']
    next_page = current_page + 1 if current_page < total_pages else total_pages
    prev_page = current_page - 1 if current_page > 1 else 1

    pages = {
        'total_pages': total_pages,
        'next_page': next_page,
        'prev_page': prev_page
    }

    return pages


@app.route('/about')
def about():
    return render_template('about.html', all_genres=ALL_GENRES)

@app.route('/search', methods=['GET', 'POST'])
async def search():
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

    params.update({
        'page': current_page,
        'sort': sort,
        'order_by': order_by
        })

    session['search'] = params

    if params:
        search_data = await search_anime(params)

        pages = await pagination(search_data, current_page)
        total_pages = pages['total_pages']
        next_page = pages['next_page']
        prev_page = pages['prev_page']

        anime_results = search_data['data']

        results_total = search_data['pagination']['items']['total']


        return render_template('results.html', anime_results=anime_results, params=params, order_by=order_by,
                               orders=ORDERS, sort=sort, all_genres=ALL_GENRES,
                                current_page=current_page, next_page=next_page, prev_page=prev_page, total_pages=total_pages, results_total=results_total)

    # user reached route via GET (as by clicking a link or via redirect)
    return apology(f"search isn't working, {session['search']}", 400)



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

# search anime with parameters
async def search_anime(params):
    url = f"{JIKAN_BASE_URL}/anime?sort=desc&sfw"
    response = requests.get(url, params=params)
    results = response.json()
    return results


@app.route('/genres')
async def genres():
    return render_template('genres.html', all_genres=ALL_GENRES)

@app.route('/genre')
async def genre_page():
    genre_id = request.args.get('id', default='', type=str)
    # genre_name = request.args.get('name', default='', type=str)
    current_page = request.args.get('page', default=1, type=int)
    sort = request.args.get('sort', default='desc', type=str)
    order_by = request.args.get('order_by', default='score', type=str)

    params = {
        'genres': genre_id,
        'page': current_page,
        'sort': sort,
        'order_by': order_by
        }

    genre_data = await search_anime(params)
    pages = await pagination(genre_data, current_page)
    total_pages = pages['total_pages']
    next_page = pages['next_page']
    prev_page = pages['prev_page']

    genre = [genre for genre in ALL_GENRES if any(value == int(genre_id) for value in genre.values())]
    genre_name = genre[0]['name']
    genre_description = genre[0]['description']

    genre_results = genre_data['data']

    results_total = genre_data['pagination']['items']['total']

    return render_template('genre-results.html', genre_results=genre_results, results_total=results_total, genre_description=genre_description,
                            genre_id=genre_id, genre_name=genre_name, order_by=order_by, orders=ORDERS, sort=sort, all_genres=ALL_GENRES,
                            total_pages=total_pages, next_page=next_page, prev_page=prev_page, current_page=current_page)


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
    latest_episode = await episode_number(episodes, details, animeid)

    recommendations = anime_details[2]['data']

    return render_template('anime-page.html', details=details, episodes=episodes, latest_episode=latest_episode,
                           recommendations=recommendations, all_genres=ALL_GENRES)


async def empty_details(details):
    detail = ['type', 'studios', 'rating', 'score', 'rank', 'studios', 'relations', 'images', 'demographics']

    for item in detail:
        # if item is nulll
        if not details[item]:
            details[item] = '¯_(ツ)_/¯'

    return details

async def episode_number(episodes, details, animeid):
    latest_episode = None
    detail_url = f"{JIKAN_BASE_URL}/anime/{animeid}"

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
        if not details['episodes']:
            latest_episode = 0
        else:
            latest_episode = details['episodes']
    else:
        episodes_data = episodes['data'][-1]
        latest_episode = episodes_data['mal_id']

    return latest_episode

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
