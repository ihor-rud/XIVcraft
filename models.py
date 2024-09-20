from pydantic import BaseModel


class Ingredient(BaseModel):
    id: str
    name: str
    amount: int

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, value) -> bool:
        return self.id == value.id


class Recipe(BaseModel):
    id: str
    name: str
    ingredients: list[Ingredient]
