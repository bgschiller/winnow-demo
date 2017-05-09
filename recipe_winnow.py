from winnow import Winnow

RECIPE_SOURCES = [
    # standard sources
    dict(
        data_source='Name',
        column='name',
        value_types=['string'],
    ),
    dict(
        data_source='Date Published',
        column='date_published',
        value_types=['absolute_date', 'relative_date'],
    ),
    dict(
        data_source='Description',
        column='description',
        value_types=['string'],
    ),

    # special sources
    dict(
        data_source='Prep Time (minutes)',
        column='(EXTRACT(EPOCH FROM prep_time)::int / 60)',
        value_types=['numeric'],
    ),
    dict(
        data_source='Cook Time (minutes)',
        column='(EXTRACT(EPOCH FROM cook_time)::int / 60)',
        value_types=['numeric'],
    ),
    dict(
        data_source='Ingredients',
        value_types=['collection'],
    ),
    dict(
        data_source='Suitable for Diet',
        value_types=['collection'],
        picklist_values=[
            'vegan',
            'vegetarian',
            'glutenfree',
            'halal',
            'kosher',
        ]
    ),
]


class RecipeWinnow(Winnow):
    def __init__(self):
        super().__init__('recipe', RECIPE_SOURCES)

    # This is ugly, and I wish I knew a better way to seperate these values.
    # maybe just pass them in at initialization?
    _special_cases = {}


@RecipeWinnow.special_case('Ingredients', 'collection')
def ingredients(rw, clause):
    return rw.sql.prepare_query(
        '''
        {% if not_any_of %}
            NOT
        {% endif %}
        id = ANY(
            SELECT recipe_id FROM ingredient
            {% for ix, ing in enumerate(value) %}
                , plainto_tsquery('english', {{ ing }}) "q{{ ix }}"
            {% endfor %}
            WHERE
            {% for ix, ing in enumerate(value) %}
                to_tsvector('english', ingredient_text) @@ "q{{ ix }}"
                {% if not loop.last %} OR {% endif %}
            {% endfor %}
        )
        ''',
        value=clause['value_vivified'],
        not_any_of=clause['operator'] == 'not any of',
    )


@RecipeWinnow.special_case('Suitable for Diet', 'collection')
def diet_suitability(rw, clause):
    return rw.sql.prepare_query(
        '''
        {% if not_any_of %}
            NOT
        {% endif %}
        id = ANY(
            SELECT recipe_id FROM diet_suitability
            WHERE diet = ANY(VALUES {{ value | pg_array }})
        )
        ''',
        value=clause['value_vivified'],
        not_any_of=clause['operator'] == 'not_any_of',
    )
