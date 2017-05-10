from flask import Flask, render_template, request, jsonify, g
from recipe_winnow import RecipeWinnow
import json
import datetime
import psycopg2
import os
import copy


class HighlightingFlask(Flask):
    jinja_options = dict(Flask.jinja_options)
    jinja_options.setdefault(
        'extensions',
        []).append('jinja2_highlight.HighlightExtension')


app = HighlightingFlask(__name__)


DATABASE_URL = os.getenv('DATABASE_URL', 'dbname=winnow_recipes')


def get_db():
    if not hasattr(g, 'dbconn'):
        g.dbconn = psycopg2.connect(DATABASE_URL)
    return g.dbconn


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'dbconn'):
        g.dbconn.close()


def dictfetchall(q, params):
    db = get_db()
    with db.cursor() as c:
        print(c.mogrify(q, params).decode('utf-8'))
        c.execute(q, params)
        keys = [col[0] for col in c.description]
        return [dict(zip(keys, row)) for row in c.fetchall()]

PREDEFINED_FILTERS = [
    dict(
        name='That LA Diet',
        filt={
            'logical_op': '&',
            'filter_clauses': [
                {
                    'data_source': 'Suitable for Diet',
                    'operator': 'any of',
                    'value': ['gluten-free'],
                },
            ],
        },
        icon='<img src="/static/gluten-free-256.png">',
    ),
    dict(
        name='Meat and potatoes',
        filt={
            'logical_op': '&',
            'filter_clauses': [
                {
                    'data_source': 'Suitable for Diet',
                    'operator': 'not any of',
                    'value': ['vegetarian'],
                },
                {
                    'data_source': 'Ingredients',
                    'operator': 'any of',
                    'value': ['potato'],
                },
                {
                    'data_source': 'Ingredients',
                    'operator': 'any of',
                    'value': [
                        'beef', 'steak', 'chicken', 'pork', 'turkey', 'sausage',
                        'lamb',
                    ],
                },
            ],
        },
        icon='<img src="/static/meat_and_potat.png">'
    ),
    dict(
        name='Quick, use the tomatoes!',
        filt={
            'logical_op': '&',
            'filter_clauses': [
                {
                    'data_source': 'Cook Time (minutes)',
                    'operator': '<=',
                    'value': 5,
                },
                {
                    'data_source': 'Ingredients',
                    'operator': 'any of',
                    'value': ['tomatoes'],
                },
            ],
        },
        icon='<img src="/static/meat_and_potat.png">'
    ),
]



GLUTEN_FREE_RESULTS = [
    {
        'cook_time': '00:05:00',
        'date_published': datetime.datetime(2009, 9, 6, 0, 0),
        'description': 'A twist on the classic, I use crisp brown rice cereal slathered in a decadent peanut butter maple syrup sludge. This version of treats has bits of chopped, toasted pistachios throughout - also vegan (no marshmallows) and gluten-free.',
        'id': 865,
        'img_url': 'http://www.101cookbooks.com/mt-static/images/food/pb_rice_crispy_treats.jpg',
        'name': 'Peanut Butter Krispy Treats',
        'prep_time': '00:10:00',
        'url': 'http://www.101cookbooks.com/archives/peanut-butter-krispy-treats-recipe.html',
        'yield': ''},
    {
        'cook_time': None,
        'date_published': datetime.datetime(2007, 10, 22, 0, 0),
        'description': 'A grown-up twist on the figgy classic. This filling for this fig cookie recipe is dried figs that are marinated overnight in port and pomegranate juice and then pureed. They also happen to be gluten-free.',
        'id': 957,
        'img_url': 'http://www.101cookbooks.com/mt-static/images/food/figcookierecipe_07.jpg',
        'name': 'Grown-up Fig Cookies',
        'prep_time': None,
        'url': 'http://www.101cookbooks.com/archives/grownup-fig-cookies-recipe.html',
        'yield': ''}]


def find_where(lst, **kwargs):
    for val in lst:
        for k, v in kwargs.items():
            if val.get(k) != v:
                break  # not a match
        else:  # Every k,v matches.
            return val
    return None


@app.route('/', methods=['GET', 'POST'])
def index():

    chosen_filt = find_where(PREDEFINED_FILTERS, name=request.form.get('predefined'))

    if request.method == 'POST':
        filt = chosen_filt['filt'] if chosen_filt else json.loads(request.form['filter-json-input'])
        results = prepare_and_perform_query(filt)
    else:
        filt = None
        results = None
        # Just for debugging
        results = prepare_and_perform_query(PREDEFINED_FILTERS[0]['filt'])

    results['params'] = json.dumps(results['params'], indent=4)
    return render_template(
        'index.html',
        chosen_filt=chosen_filt or PREDEFINED_FILTERS[0],
        user_supplied_filt=json.dumps(filt or PREDEFINED_FILTERS[0]['filt'], indent=4, sort_keys=True),
        empty_filter=json.dumps(RecipeWinnow.empty_filter(), indent=4, sort_keys=True),
        predefined_filters=PREDEFINED_FILTERS,
        results=results,
    )


def strip_empty_lines(text):
    return '\n'.join(filter(None, (line.strip() for line in text.split('\n'))))


@app.route('/recipe-filter', methods=['POST'])
def recipe_filter():
    filt = PREDEFINED_FILTERS.get(
        request.form['predefined'],
        request.form['filter-json-input'])
    return jsonify(prepare_and_perform_query(filt))


def prepare_and_perform_query(filt):
    rw = RecipeWinnow()

    sql = rw.query(copy.deepcopy(filt))
    rows = dictfetchall(*sql)
    return dict(query=strip_empty_lines(sql.query), params=sql.params, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
