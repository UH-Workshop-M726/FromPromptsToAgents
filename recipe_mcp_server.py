import json
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Recipe Agent")

def load_dishes():
    """Loads the dish database from the data folder."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data", "dish_database.json")
    
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return []

@mcp.tool()
def fit_budget(budget: float, servings: int = 2) -> str:
    """Finds all dishes where (unit price * servings) is within the budget."""
    dishes = load_dishes()
    results = []
    
    for d in dishes:
        total_cost = d.get("price_gbp", 0) * servings
        if total_cost <= budget:
            results.append(f"{d['name']} (Total Cost: £{total_cost:.2f})")
    
    if not results:
        return f"No dishes found within a £{budget} budget for {servings} people."
    
    return "Budget-friendly options:\n" + "\n".join(results)

@mcp.tool()
def get_nutrition_comparison(dish_names: list[str]) -> str:
    dishes = load_dishes()
    comparison = []
    
    for name in dish_names:
        for d in dishes:
            if d["name"].lower() == name.lower():
                stats = (
                    f"**{d['name']}**:\n"
                    f"- Protein: {d.get('protein_g', 0)}g\n"
                    f"- Calories: {d.get('calories_kcal', 0)} kcal\n"
                    f"- Vegetarian: {'Yes' if d.get('is_vegetarian') else 'No'}\n"
                )
                comparison.append(stats)
                
    return "\n".join(comparison) if comparison else "Nutritional data not found for those selections."

if __name__ == "__main__":
    mcp.run()