from flask import Flask, render_template, request, jsonify, g, flash
from recipe_winnow import RecipeWinnow
from winnow.error import WinnowError
import json
from json.decoder import JSONDecodeError
import psycopg2
import os
import copy


class HighlightingFlask(Flask):
    jinja_options = dict(Flask.jinja_options)
    jinja_options.setdefault(
        'extensions',
        []).append('jinja2_highlight.HighlightExtension')


app = HighlightingFlask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'moosesoup4you')


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
        icon='/static/gluten-free-256.png',
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
        icon='/static/meat_and_potat.png'
    ),
    dict(
        name='Quick, the tomatoes!',
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
        icon='/static/tomato.png'
    ),
    dict(
        name='Cookie monster',
        filt={
            'logical_op': '&',
            'filter_clauses': [
                {
                    'data_source': 'name',
                    'operator': 'contains',
                    'value': 'cookie',
                },
            ],
        },
        icon='/static/tomato.png',
    ),
]


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
        try:
            filt = chosen_filt['filt'] if chosen_filt else json.loads(request.form['filter-json-input'])
            results = prepare_and_perform_query(filt)
            results['params'] = json.dumps(results['params'], indent=4)
        except WinnowError as e:
            filt = results = None
            flash(e, 'error')
        except JSONDecodeError:
            filt = results = None
            flash("Filter is invalid JSON", 'error')
    else:
        filt = results = None

    return render_template(
        'index.html',
        chosen_filt_name=request.form.get('predefined') or PREDEFINED_FILTERS[0]['name'],
        user_supplied_filt=request.form.get('filter-json-input') or json.dumps(PREDEFINED_FILTERS[0]['filt'], indent=4, sort_keys=True),
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

    where_clauses = rw.where_clauses(copy.deepcopy(filt))
    sql = rw.prepare_query(
        'SELECT * FROM recipe WHERE {{ where_clauses }} LIMIT 10',
        where_clauses=where_clauses)
    rows = dictfetchall(*sql)
    return dict(query=strip_empty_lines(sql.query), params=sql.params, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
