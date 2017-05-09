from flask import Flask, render_template, request, redirect, jsonify
from recipe_winnow import RecipeWinnow

app = Flask(__name__)


PREDEFINED_FILTERS = {
    'Gluten-free w/ Tomatoes': {
        'logical_op': '&',
        'filter_clauses': [
            {
                'data_source': 'Suitable for Diet',
                'operator': 'any of',
                'value': ['glutenfree'],
            },
            {
                'data_source': 'Ingredients',
                'operator': 'any of',
                'value': ['tomatoe'],
            },
        ]
    },
}


@app.route('/')
def index():
    return render_template(
        'index.html',
        predefined_filters=PREDEFINED_FILTERS
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
