DROP TABLE IF EXISTS recipe;
CREATE TABLE recipe (
    id bigint primary key,
    name varchar(63),
    date_published timestamp,
    url varchar(255),
    img_url varchar(255),
    prep_time varchar(31),
    cook_time varchar(31),
    yield varchar(31),
    description varchar(580)
);

DROP TABLE IF EXISTS ingredient;
CREATE TABLE ingredient (
    recipe_id bigint NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    ingredient_text varchar(225)
);

DROP TABLE IF EXISTS diet_suitability;
CREATE TABLE diet_suitability(
    recipe_id bigint NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    diet varchar(31)
);
