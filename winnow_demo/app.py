from flask import Flask, render_template, request, redirect, jsonify
from recipe_winnow import RecipeWinnow
import json
import datetime

app = Flask(__name__)


PREDEFINED_FILTERS = {
    'That LA Diet': {
        'logical_op': '&',
        'filter_clauses': [
            {
                'data_source': 'Suitable for Diet',
                'operator': 'any of',
                'value': ['glutenfree'],
            },
        ]
    },
}

# Throw some fake filters in for testing the frontend
for other_name in (
        'Meat-eaters', 'Veggie',
        'Quick! use the strawberries before they go bad'):
    PREDEFINED_FILTERS[other_name] = json.loads(json.dumps(PREDEFINED_FILTERS['That LA Diet']))


GLUTEN_FREE_RESULTS = [{'cook_time': '00:05:00',
  'date_published': datetime.datetime(2009, 9, 6, 0, 0),
  'description': 'A twist on the classic, I use crisp brown rice cereal slathered in a decadent peanut butter maple syrup sludge. This version of treats has bits of chopped, toasted pistachios throughout - also vegan (no marshmallows) and gluten-free.',
  'id': 865,
  'img_url': 'http://www.101cookbooks.com/mt-static/images/food/pb_rice_crispy_treats.jpg',
  'name': 'Peanut Butter Krispy Treats',
  'prep_time': '00:10:00',
  'url': 'http://www.101cookbooks.com/archives/peanut-butter-krispy-treats-recipe.html',
  'yield': ''},
 {'cook_time': None,
  'date_published': datetime.datetime(2007, 10, 22, 0, 0),
  'description': 'A grown-up twist on the figgy classic. This filling for this fig cookie recipe is dried figs that are marinated overnight in port and pomegranate juice and then pureed. They also happen to be gluten-free.',
  'id': 957,
  'img_url': 'http://www.101cookbooks.com/mt-static/images/food/figcookierecipe_07.jpg',
  'name': 'Grown-up Fig Cookies',
  'prep_time': None,
  'url': 'http://www.101cookbooks.com/archives/grownup-fig-cookies-recipe.html',
  'yield': ''}]

@app.route('/')
def index():
    rw = RecipeWinnow()

    sql = rw.where_clauses(json.loads(json.dumps(PREDEFINED_FILTERS['That LA Diet'])))

    return render_template(
        'index.html',
        predefined_filters=PREDEFINED_FILTERS,
        sql_results=sql,
        db_results=GLUTEN_FREE_RESULTS,
    )


def strip_empty_lines(text):
    return '\n'.join(filter(None, (line.strip() for line in text.split('\n'))))


@app.route('/recipe-filter', methods=['GET', 'POST'])
def recipe_filter():
    if request.method == 'GET':
        return redirect('/')
    rw = RecipeWinnow()
    filt = PREDEFINED_FILTERS.get(
        request.form['predefined'],
        request.form['filter-json-input'])
    sql = rw.where_clauses(filt)
    return jsonify(dict(query=strip_empty_lines(sql.query), params=sql.params))

if __name__ == '__main__':
    app.run(debug=True)
