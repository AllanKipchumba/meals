
import re

def adjust_ingredient_quantity(ingredient: str, multiplier: float) -> str:
    """Adjust ingredient quantity based on serving multiplier"""
    if multiplier == 1:
        return ingredient

    # Handle ingredients with weights in parentheses
    weight_pattern = r'.*?\(([\d.]+)\s*([a-zA-Z]+)\)\s*([^()]+)'
    weight_match = re.match(weight_pattern, ingredient)
    if weight_match:
        qty = float(weight_match.group(1)) * multiplier
        unit = weight_match.group(2)
        item = weight_match.group(3).strip()
        
        # Convert the weight with the new quantity
        from utils.shopping_list import convert_weight
        weight_str = convert_weight(qty, unit)
        return f"{item} ({weight_str})"

    # Pattern to match quantities at the start of the ingredient string
    pattern = r'^([\d.\/]+)\s*([a-zA-Z]+|\([^)]+\))?\s*(.+)$'
    match = re.match(pattern, ingredient)
    
    if not match:
        return ingredient
        
    qty_str, unit, item = match.groups()
    
    # Convert fractions to decimals
    if '/' in qty_str:
        num, denom = map(float, qty_str.split('/'))
        quantity = num / denom
    else:
        quantity = float(qty_str)
    
    # Adjust quantity
    new_qty = quantity * multiplier
    
    # If it's a weight unit, use convert_weight
    if unit and unit.lower() in ['g', 'grams', 'gram', 'oz', 'ounces', 'lb', 'lbs', 'pounds']:
        from utils.shopping_list import convert_weight
        return f"{item} ({convert_weight(new_qty, unit)})"
    
    # Format the new quantity (keep it to 1 decimal place if not whole number)
    if new_qty.is_integer():
        new_qty_str = str(int(new_qty))
    else:
        new_qty_str = f"{new_qty:.1f}"
    
    # Reconstruct the ingredient string
    if unit:
        return f"{new_qty_str} {unit} {item}"
    return f"{new_qty_str} {item}"


import pandas as pd
import plotly.express as px
from database.queries import Database

def calculate_nutrition_totals(recipes):
    """Calculate total nutrition for a list of recipes"""
    totals = {
        'calories': sum(r['calories'] for r in recipes),
        'protein': sum(r['protein'] for r in recipes),
        'carbs': sum(r['carbs'] for r in recipes),
        'fat': sum(r['fat'] for r in recipes)
    }
    return totals

def create_nutrition_chart(nutrition_data):
    """Create a pie chart of nutritional information"""
    df = pd.DataFrame({
        'Nutrient': ['Protein', 'Carbs', 'Fat'],
        'Grams': [nutrition_data['protein'], 
                 nutrition_data['carbs'], 
                 nutrition_data['fat']]
    })
    
    fig = px.pie(df, values='Grams', names='Nutrient',
                 title='Macronutrient Distribution')
    return fig

def filter_recipes(preferences, allergies, max_calories=None):
    """Filter recipes based on user preferences and restrictions"""
    db = Database()
    recipes = db.get_recipes()
    
    filtered = []
    for recipe in recipes:
        if all(pref in recipe['tags'] for pref in preferences) and \
           not any(allergy in recipe['ingredients'] for allergy in allergies):
            if max_calories is None or recipe['calories'] <= max_calories:
                filtered.append(recipe)
    
    return filtered

def generate_shopping_list(recipes):
    """Generate a consolidated shopping list from multiple recipes"""
    shopping_list = {}
    
    for recipe in recipes:
        for ingredient, amount in recipe['ingredients'].items():
            if ingredient in shopping_list:
                shopping_list[ingredient]['amount'] += amount['amount']
            else:
                shopping_list[ingredient] = amount.copy()
    
    return shopping_list


def format_recipe_for_printing(recipe):
    """Format a recipe into a printable text format"""
    output = []
    
    # Title
    output.append(f"\n{'=' * 50}")
    output.append(f"{recipe['name'].upper()}")
    output.append(f"{'=' * 50}\n")
    
    # Basic Info
    output.append(f"Cooking Time: {recipe['cooking_time']} minutes")
    output.append(f"Calories: {recipe['calories']}")
    output.append(f"Difficulty: {recipe['difficulty']}\n")
    
    # Macros
    output.append("NUTRITIONAL INFORMATION")
    output.append("-" * 30)
    output.append(f"Protein: {recipe['macros']['protein']}g")
    output.append(f"Carbs: {recipe['macros']['carbs']}g")
    output.append(f"Total Fat: {recipe['macros']['total_fat']}g")
    output.append(f"Saturated Fat: {recipe['macros']['saturated_fat']}g\n")
    
    # Ingredients
    output.append("INGREDIENTS")
    output.append("-" * 30)
    for ingredient in recipe['ingredients']:
        output.append(f"• {ingredient}")
    output.append("")
    
    # Weekend Prep
    if 'weekend_prep' in recipe:
        output.append("WEEKEND PREP")
        output.append("-" * 30)
        for i, step in enumerate(recipe['weekend_prep'], 1):
            output.append(f"{i}. {step}")
        output.append("")
    
    # Instructions
    output.append("COOKING INSTRUCTIONS")
    output.append("-" * 30)
    for i, instruction in enumerate(recipe['instructions'], 1):
        output.append(f"{i}. {instruction}")
    output.append("\n")
    
    return "\n".join(output)
