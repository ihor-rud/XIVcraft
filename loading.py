import json
import typing
import requests
from pathlib import Path
from os import getenv

from pydantic import parse_file_as
from pydantic.json import pydantic_encoder
from models import Ingredient, Recipe


XIVAPI_URL = "https://xivapi.com"
DEFAULT_PARAMS = {"private_key": getenv("XIVAPI_KEY")}


def make_request(url: str, params: dict = {}):
    resp = requests.get(
        XIVAPI_URL + url,
        params={**DEFAULT_PARAMS, **params},
    )
    return resp.json()


def load_recipes() -> list[Recipe]:
    query = {"indexes": "Recipe", "string": "Diadochos *"}
    resp = make_request("/search", query)
    recipes = []
    for result in resp["Results"]:
        url = result["Url"]
        ingredients_resp = make_request(url)
        ingredients = []

        id = ingredients_resp["ItemResultTargetID"]
        name = result["Name"]

        for i in range(8):
            if ingredients_resp.get(f"ItemIngredient{i}") is None:
                continue

            ingredient_id = ingredients_resp[f"ItemIngredient{i}"]["ID"]
            ingredient_name = ingredients_resp[f"ItemIngredient{i}"]["Name"]
            ingredient_amount = ingredients_resp[f"AmountIngredient{i}"]
            ingredients.append(
                Ingredient(
                    id=str(ingredient_id),
                    name=ingredient_name,
                    amount=ingredient_amount,
                )
            )

        recipes.append(Recipe(id=str(id), name=name, ingredients=ingredients))
    return recipes


def dump_to_json(path: str):
    recipes = load_recipes()
    with open(path, mode="a+") as out:
        json.dump(recipes, out, default=pydantic_encoder)


def from_json(path: str) -> list[Recipe]:
    if not Path.exists(path):
        dump_to_json(path)

    return parse_file_as(typing.List[Recipe], path)
