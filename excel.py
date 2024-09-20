import requests
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range_abs

from models import Ingredient, Recipe

UNIVERSALIS_URL = "https://universalis.app"


def load_ingredient_prices(ingredients: list[Ingredient]) -> dict[str, int]:
    ids = ",".join(ingredient.id for ingredient in ingredients)
    resp = requests.get(
        UNIVERSALIS_URL + f"/api/v2/Chaos/{ids}",
        params={"listings": 10},
    )
    resp = resp.json()
    result = dict()
    resp = resp["items"]
    for ingredient in ingredients:
        for listing in resp[ingredient.id]["listings"]:
            if listing["quantity"] > 30:
                break
        else:
            listing = resp[ingredient.id]["listings"][-1]

        result[ingredient.name] = listing["pricePerUnit"]

    return result


def load_item_prices(recipes: list[Recipe]) -> dict[str, int]:
    ids = ",".join(recipe.id for recipe in recipes)
    resp = requests.get(
        UNIVERSALIS_URL + f"/api/v2/Omega/{ids}",
        params={"listings": 1, "hq": True},
    ).json()
    result = dict()
    resp = resp["items"]
    for recipe in recipes:
        try:
            listing = resp[recipe.id]["listings"][0]
            result[recipe.name] = listing["pricePerUnit"]
        except IndexError:
            result[recipe.name] = 0

    return result


def generate_xlsx(path: str, recipes: list[Recipe]):
    unique_ingredients = list(
        {ingredient for recipe in recipes for ingredient in recipe.ingredients}
    )

    workbook = xlsxwriter.Workbook(path)
    recipes_worksheet = workbook.add_worksheet("recipes")

    for i, recipe in enumerate(recipes):
        recipes_worksheet.write(i + 1, 0, recipe.name)

    for i, item in enumerate(unique_ingredients):
        recipes_worksheet.write(0, i + 1, item.name)

    for row, item in enumerate(recipes):
        for ingredient in item.ingredients:
            coll = unique_ingredients.index(ingredient)
            recipes_worksheet.write_number(row + 1, coll + 1, ingredient.amount)

    prices_worksheet = workbook.add_worksheet("prices")
    ingredient_prices = load_ingredient_prices(unique_ingredients)

    for row, (key, val) in enumerate(ingredient_prices.items()):
        prices_worksheet.write(row, 0, key)
        prices_worksheet.write_number(row, 1, val)

    item_prices = load_item_prices(recipes)
    for row, (key, val) in enumerate(item_prices.items()):
        prices_worksheet.write(row, 3, key)
        prices_worksheet.write_number(row, 4, val)

    results_worksheet = workbook.add_worksheet("results")
    results_worksheet.write(0, 1, "Sell price")
    results_worksheet.write(0, 2, "Craft price")
    results_worksheet.write(0, 3, "Difference")
    results_worksheet.write(0, 4, "Amount")

    for row, item in enumerate(recipes):
        results_worksheet.write(row + 1, 0, item.name)

    for row, item in enumerate(recipes):
        results_worksheet.write(row + 1, 0, item.name)

        craft_price = xl_rowcol_to_cell(row + 1, 2)
        recipes_range = xl_range_abs(row + 1, 1, row + 1, len(unique_ingredients))
        prices_range = xl_range_abs(0, 1, len(unique_ingredients) - 1, 1)
        results_worksheet.write_array_formula(
            craft_price,
            f"{{=SUMPRODUCT(recipes!{recipes_range}, TRANSPOSE(prices!{prices_range}))}}",
        )

        sell_price = xl_rowcol_to_cell(row + 1, 1)
        results_worksheet.write_formula(sell_price, f"=prices!$E${row + 1}")

        results_worksheet.write_formula(row + 1, 3, f"={sell_price} - {craft_price}")

    for i, item in enumerate(unique_ingredients):
        results_worksheet.write(0, i + 6, item.name)
        recipes_range = xl_range_abs(1, i + 1, len(recipes), i + 1)

        results_worksheet.write_array_formula(
            1,
            i + 6,
            1,
            i + 6,
            f"{{=SUMPRODUCT(E2:E{1 + len(recipes)}, recipes!{recipes_range})}}",
        )

    workbook.close()
