import re
from typing import Tuple, Dict, List
from utils.recipe_utils import adjust_ingredient_quantity

def convert_weight(quantity: float, unit: str) -> str:
    """
    Convert between metric and US weight units.
    Returns string with both units if applicable.
    """
    if unit.lower() in ['g', 'grams', 'gram']:
        lbs = quantity * 0.00220462
        if quantity >= 1000:
            kg = quantity/1000
            lbs = kg * 2.20462
            return f"{kg:.1f}kg ({lbs:.1f} lbs)"
        elif lbs >= 1:
            return f"{quantity:.0f}g ({lbs:.1f} lbs)"
        else:
            oz = quantity * 0.035274
            return f"{quantity:.0f}g ({oz:.1f} oz)"
    elif unit.lower() in ['oz', 'ounces', 'ounce']:
        grams = quantity * 28.3495
        if quantity >= 16:
            return f"{grams/1000:.1f}kg ({quantity/16:.1f} lbs)"
        else:
            return f"{grams:.0f}g ({quantity:.1f} oz)"
    elif unit.lower() in ['lb', 'lbs', 'pounds', 'pound']:
        kg = quantity * 0.453592
        return f"{kg*1000:.0f}g ({quantity:.1f} lbs)"
    return f"{quantity:.1f} {unit}"

def parse_ingredient(ingredient: str, serving_multiplier: float = 1.0) -> Tuple[float, str, str, str]:
    """
    Parse an ingredient string into quantity, unit, descriptor, and item.
    Returns (quantity, unit, descriptor, item)
    """
    # Pattern for ingredients with weight in parentheses
    # First try to extract weight in parentheses (e.g., "(500g chicken)")
    weight_pattern = r'.*?\(([\d.]+)\s*([a-zA-Z]+)\)\s*([^()]+)'
    weight_match = re.match(weight_pattern, ingredient)
    if weight_match:
        qty = float(weight_match.group(1)) * serving_multiplier
        unit = weight_match.group(2)
        item = weight_match.group(3).strip()
        return (qty, unit, "", item)

    # If no parentheses weight found, try start of string (e.g., "500g chicken")
    start_pattern = r'^([\d.]+)\s*([a-zA-Z]+)\s*(.+)'
    start_match = re.match(start_pattern, ingredient)
    if start_match:
        qty = float(start_match.group(1)) * serving_multiplier
        unit = start_match.group(2)
        item = start_match.group(3).strip()
        return (qty, unit, "", item)

    # Pattern for regular quantities with possible descriptors
    pattern = r'^([\d.\/]+)\s*([a-zA-Z]+)?\s*(large|small|medium|bunch|head|whole)?\s*(.+)$'
    match = re.match(pattern, ingredient.lower())

    if not match:
        return (1.0, "", "", ingredient.strip())

    qty_str, unit, descriptor, item = match.groups()

    # Convert fractions to decimals
    if '/' in qty_str:
        num, denom = map(float, qty_str.split('/'))
        quantity = (num / denom) * serving_multiplier
    else:
        quantity = float(qty_str) * serving_multiplier

    return (
        quantity,
        unit.lower() if unit else "",
        descriptor.lower() if descriptor else "",
        item.strip()
    )

def standardize_unit(unit: str) -> str:
    """
    Standardize unit names to a common format.
    """
    unit_mapping = {
        'tbsp': 'tablespoons',
        'tbs': 'tablespoons',
        'tablespoon': 'tablespoons',
        'tsp': 'teaspoons',
        'teaspoon': 'teaspoons',
        'cup': 'cups',
        'oz': 'ounces',
        'ounce': 'ounces',
        'lb': 'pounds',
        'pound': 'pounds',
        'g': 'grams',
        'gram': 'grams',
        'ml': 'milliliters',
        'milliliter': 'milliliters',
        'l': 'liters',
        'liter': 'liters'
    }
    return unit_mapping.get(unit.lower(), unit.lower())

def can_combine_units(unit1: str, unit2: str) -> bool:
    """
    Determine if two units can be combined.
    """
    # Standardize units first
    unit1, unit2 = standardize_unit(unit1), standardize_unit(unit2)

    # Group compatible units
    volume_units = {'cups', 'tablespoons', 'teaspoons', 'milliliters', 'liters'}
    weight_units = {'grams', 'kilograms', 'ounces', 'pounds'}

    # Check if units are identical or in the same group
    return (unit1 == unit2) or \
           (unit1 in volume_units and unit2 in volume_units) or \
           (unit1 in weight_units and unit2 in weight_units)

def combine_ingredients(recipes: List[Dict]) -> List[str]:
    """
    Combines ingredients from multiple recipes and consolidates similar items with quantities.
    """
    ingredient_dict = {}

    for recipe in recipes:
        for ingredient in recipe["ingredients"]:
            quantity, unit, descriptor, item = parse_ingredient(ingredient)
            item_lower = item.lower()

            # Create a key that includes the descriptor if present
            key = f"{descriptor} {item}" if descriptor else item
            key_lower = key.lower()

            # Find matching ingredient or create new entry
            matched = False
            for existing_key in list(ingredient_dict.keys()):
                _, existing_unit, existing_desc, existing_item = parse_ingredient(existing_key)

                # Check if items match (ignoring descriptors for vegetables)
                if existing_item.lower() in item_lower or item_lower in existing_item.lower():
                    if descriptor or existing_desc:  # Handle vegetables with descriptors
                        if descriptor == existing_desc:  # Only combine if descriptors match
                            ingredient_dict[existing_key].append((quantity, unit))
                            matched = True
                            break
                    elif can_combine_units(unit, existing_unit):
                        # Combine quantities for non-vegetable ingredients
                        ingredient_dict[existing_key].append((quantity, unit))
                        matched = True
                        break

            if not matched:
                ingredient_dict[ingredient] = [(quantity, unit)]

    # Categorize ingredients
    categories = {
        'Meat & Seafood': [],
        'Vegetables & Fruits': [],
        'Herbs & Spices': [],
        'Grains & Pasta': [],
        'Canned Goods': [],
        'Other': []
    }
    
    meat_keywords = ['chicken', 'beef', 'pork', 'turkey', 'salmon', 'fish', 'shrimp', 'cod', 'tuna']
    vegetable_keywords = ['onion', 'carrot', 'tomato', 'lettuce', 'pepper', 'cucumber', 'potato', 'broccoli', 'spinach', 'kale', 'cabbage', 'zucchini', 'apple', 'banana', 'berry', 'berries']
    herb_spice_keywords = ['basil', 'thyme', 'oregano', 'parsley', 'cilantro', 'mint', 'sage', 'rosemary', 'salt', 'pepper', 'cumin', 'paprika', 'cinnamon', 'garlic', 'powder', 'chili', 'seasoning', 'spice', 'herb']
    grain_keywords = ['rice', 'quinoa', 'pasta', 'noodle', 'flour', 'bread', 'oat', 'cereal', 'grain', 'couscous', 'barley']
    canned_keywords = ['can', 'canned', 'tin', 'jarred', 'preserved', 'paste', 'sauce', 'broth', 'stock']

    for ingredient, quantities in ingredient_dict.items():
        quantity, unit, descriptor, item = parse_ingredient(ingredient)
        item_lower = item.lower()

        # Format the ingredient string
        if len(quantities) > 1 and unit and not descriptor:
            total_qty = sum(qty for qty, _ in quantities)
            if unit.lower() in ['g', 'grams', 'gram', 'oz', 'ounces', 'lb', 'lbs', 'pounds']:
                converted = convert_weight(total_qty, unit)
                formatted_item = f"{item} ({converted} - needed for {len(quantities)} recipes)"
            else:
                std_unit = standardize_unit(quantities[0][1])
                formatted_item = f"{item} ({total_qty:.1f} {std_unit} - needed for {len(quantities)} recipes)"
        elif len(quantities) > 1 and descriptor:
            formatted_item = f"{descriptor} {item} (needed for {len(quantities)} recipes)"
        else:
            if unit and unit.lower() in ['g', 'grams', 'gram', 'oz', 'ounces', 'lb', 'lbs', 'pounds']:
                converted = convert_weight(quantity, unit)
                formatted_item = f"{item} ({converted})"
            elif descriptor:
                formatted_item = f"{quantity:.0f} {descriptor} {item}"
            else:
                formatted_item = f"{item} ({quantity:.1f} {unit})" if unit else item

        # Categorize the ingredient
        if any(keyword in item_lower for keyword in meat_keywords):
            categories['Meat & Seafood'].append(formatted_item)
        elif any(keyword in item_lower for keyword in vegetable_keywords) or descriptor in ['large', 'small', 'medium', 'bunch', 'head']:
            categories['Vegetables & Fruits'].append(formatted_item)
        elif any(keyword in item_lower for keyword in herb_spice_keywords) or 'powder' in item_lower or 'seasoning' in item_lower:
            categories['Herbs & Spices'].append(formatted_item)
        elif any(keyword in item_lower for keyword in grain_keywords):
            categories['Grains & Pasta'].append(formatted_item)
        elif any(keyword in item_lower for keyword in canned_keywords):
            categories['Canned Goods'].append(formatted_item)
        else:
            categories['Other'].append(formatted_item)

    # Create final shopping list with categories
    shopping_list = []
    for category, items in categories.items():
        if items:  # Only add category if it has items
            shopping_list.append(f"\n{category}:")
            shopping_list.extend([f"• {item}" for item in sorted(items)])

    return shopping_list

def generate_shopping_list(recipes: List[Dict], serving_multipliers: List[float] = None) -> List[str]:
    """
    Generates a shopping list from a list of recipes.
    Args:
        recipes: List of recipe dictionaries
        serving_multipliers: List of serving multipliers for each recipe
    """
    if not recipes:
        return []

    if serving_multipliers is None:
        serving_multipliers = [1.0] * len(recipes)

    # Create new recipe list with adjusted ingredients
    adjusted_recipes = []
    for recipe, multiplier in zip(recipes, serving_multipliers):
        adjusted_recipe = recipe.copy()
        adjusted_recipe["ingredients"] = [
            adjust_ingredient_quantity(ingredient, multiplier)
            for ingredient in recipe["ingredients"]
        ]
        adjusted_recipes.append(adjusted_recipe)

    return combine_ingredients(adjusted_recipes)