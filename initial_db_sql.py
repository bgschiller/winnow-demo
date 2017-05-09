from collections import namedtuple
import isodate
import json
from dateutil.parser import parse as date_parse

Recipe = namedtuple(
    'Recipe',
    'id name date_published url img_url prep_time cook_time yield_ description'
)
Ingredient = namedtuple('Ingredient', 'recipe_id ingredient_text')
DietaryRestriction = namedtuple('DietaryRestriction', 'recipe_id diet')

DIETS = {  # diet -> [list of implied diets]
    'vegan': ['vegan', 'vegetarian', 'halal', 'kosher'],
    'vegetarian': ['vegetarian', 'halal', 'kosher'],
    'glutenfree': ['gluten-free'],
    'halal': ['halal', 'kosher'],
    'kosher': ['kosher', 'halal'],
}


def try_parse_duration(dur):
    if not dur:
        return None
    try:
        return isodate.parse_duration(dur)
    except isodate.ISO8601Error:
        return None


def schematize_recipe(recipe_id, recipe):
    r = Recipe(
        id=recipe_id,
        name=recipe['name'],
        date_published=date_parse(recipe['datePublished']),
        url=recipe['url'],
        img_url=recipe['image'],
        cook_time=try_parse_duration(recipe['cookTime']),
        prep_time=try_parse_duration(recipe['prepTime']),
        yield_=recipe['recipeYield'],
        description=recipe['description'],
    )
    if len(r.description) > 580:
        return  # too long for db
    yield r

    for ing in recipe['ingredients'].split('\n'):
        yield Ingredient(
            recipe_id=recipe_id,
            ingredient_text=ing,
        )

    dietary_restr = (r.name + r.description + r.url).lower().replace('-', '')
    satisfied_diets = {
        diet for diet_string in DIETS for diet in DIETS[diet_string]
        if diet_string in dietary_restr
    }
    for diet in satisfied_diets:
        yield DietaryRestriction(recipe_id, diet)


def insert_stmt(row):
    if isinstance(row, Recipe):
        return '''
    INSERT INTO recipe(
        id, name, date_published, url, img_url,
        prep_time, cook_time, yield, description)
    VALUES
        (%(id)s, %(name)s, %(date_published)s, %(url)s, %(img_url)s,
         %(prep_time)s, %(cook_time)s, %(yield_)s, %(description)s);
         ''', row._asdict()
    elif isinstance(row, Ingredient):
        return '''
        INSERT INTO ingredient(recipe_id, ingredient_text)
        VALUES (%(recipe_id)s, %(ingredient_text)s); ''', row._asdict()
    elif isinstance(row, DietaryRestriction):
        return '''
        INSERT INTO diet_suitability(recipe_id, diet)
        VALUES (%(recipe_id)s, %(diet)s);
        ''', row._asdict()
    else:
        raise ValueError('Unrecognized row type, {}'.format(row))


INDICES = (
    '''CREATE INDEX ingredient_full_text ON ingredient
    USING gin(to_tsvector('english', ingredient_text));''',
)


def fill_db_stmts():
    with open('recipes.sql') as f:
        yield f.read(), dict()
    with open('openrecipes.jsonlines') as f:
        for ix, recipe in enumerate(f):
            for row in schematize_recipe(ix, json.loads(recipe)):
                yield insert_stmt(row)

    for index in INDICES:
        yield index, ()  # empty tuple is the query params
