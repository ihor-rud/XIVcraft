from loading import from_json
from excel import generate_xlsx

recipes = from_json("./recipes.json")
generate_xlsx("./craft.xlsx", recipes)
