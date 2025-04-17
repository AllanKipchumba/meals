import json
import os
from openai import OpenAI
import streamlit as st

# Initialize OpenAI client with error handling
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found in environment variables")
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    st.error(f"Error initializing OpenAI client: {str(e)}")
    client = None


def generate_recipe_prompt(preferences, meal_count=1, previous_recipes=None):
    dietary_restrictions = ", ".join(preferences["dietary_restrictions"])
    excluded_ingredients = ", ".join(preferences["exclude_ingredients"])
    cuisine_type = preferences["cuisine_preference"]
    cuisine_prompt = f"in {cuisine_type} cuisine style" if cuisine_type != "Any" else ""
    meal_type = preferences.get("meal_type", "dinner")
    if meal_type == "breakfast":
        meal_prompt = "Generate breakfast recipes (like omelettes, pancakes, breakfast sandwiches, oatmeal, smoothie bowls, etc.)"
    elif meal_type == "dinner":
        meal_prompt = "Generate dinner recipes (like main courses with protein, vegetables, and sides suitable for evening meals)"
    else:
        meal_prompt = "Generate recipes"

    avoid_recipes = ""
    if previous_recipes:
        avoid_recipes = f"Do not include these recipes: {', '.join([r['name'] for r in previous_recipes])}"

    recipe_count = "a recipe" if meal_count == 1 else f"{meal_count} different recipes"

    base_prompt = f"{meal_prompt} ({recipe_count}) {cuisine_prompt} based on these preferences:\n"
    preferences_text = f"""- Dietary restrictions: {dietary_restrictions}
- Maximum cooking time: {preferences["cooking_time"]} minutes
- Cooking skill level: {preferences["skill_level"]}
- Calorie range: {preferences["min_calories"]} to {preferences["max_calories"]} calories
- Macro nutrient requirements:
  * Minimum protein: {preferences["min_protein"]}g
  * Maximum carbs: {preferences["max_carbs"]}g
  * Maximum total fat: {preferences["max_total_fat"]}g
  * Maximum saturated fat: {preferences["max_saturated_fat"]}g
- Excluded ingredients: {excluded_ingredients}
{avoid_recipes}

IMPORTANT: Design these recipes to minimize weekday cooking time by maximizing weekend prep work. Include specific instructions for what can be prepared in advance during the weekend.

IMPORTANT: Each meal MUST include at least one vegetable either as part of the main course or as a side dish. The vegetable should be clearly listed in the ingredients and its preparation should be included in the instructions.

IMPORTANT: Each recipe MUST meet the specified macro nutrient requirements. Calculate and include accurate macro nutrients that are within the specified ranges.

IMPORTANT: For ingredients formatting:
1. Use descriptive quantities for vegetables (e.g., "2 large onions", "3 small carrots", "1 bunch asparagus", "1 head lettuce")
2. For weight measurements, include both metric and US units (e.g., "500g (1.1 lbs) chicken breast", "250g (8.8 oz) mushrooms")
3. Use standard kitchen measurements for other ingredients (cups, tablespoons, teaspoons)

IMPORTANT: Focus on ingredients and preparations that can be done in advance, such as:
1. Chopping vegetables
2. Preparing marinades and sauces
3. Pre-cooking grains or legumes
4. Portioning ingredients
5. Par-cooking certain components

You must respond with ONLY a valid JSON object in the following format, with no additional text:"""

    json_template = """
{
    "recipes": [
        {
            "name": "Recipe name",
            "cooking_time": "Time in minutes",
            "calories": "Calorie count",
            "macros": {
                "protein": "X grams",
                "carbs": "X grams",
                "total_fat": "X grams",
                "saturated_fat": "X grams"
            },
            "ingredients": ["2 large onions", "500g (1.1 lbs) chicken breast", "1 bunch asparagus"],
            "instructions": ["Step 1", "Step 2", "etc"],
            "weekend_prep": ["List of tasks that can be done during weekend prep", "e.g., Chop all vegetables", "Pre-cook grains"],
            "weekday_cooking": ["Quick steps to finish the dish during the week", "e.g., Heat pre-cooked components", "Final assembly"],
            "difficulty": "Skill level",
            "dietary_info": ["list", "of", "dietary", "tags"]
        }
    ]
}"""

    return base_prompt + preferences_text + json_template


def get_recipe_suggestion(preferences):
    prompt = generate_recipe_prompt(preferences)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o mini model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        recipe_data = json.loads(response.choices[0].message.content)
        return recipe_data["recipes"][0]
    except Exception as e:
        st.error(f"Error generating recipe: {str(e)}")
        return None


def get_alternative_recipe(preferences, previous_recipe):
    # Create a copy of preferences to avoid modifying the original
    alt_preferences = preferences.copy()
    
    # Get additional preferences
    additional_prefs = preferences.get("additional_preferences", [])
    
    # Create special instruction for additional preferences
    prompt = generate_recipe_prompt(alt_preferences, previous_recipes=[previous_recipe])
    
    # Add the additional preferences as a priority instruction
    if additional_prefs:
        prompt = "IMPORTANT: For this recipe generation, prioritize these user preferences over other restrictions: " + \
                ", ".join(additional_prefs) + "\n\n" + prompt
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o mini model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        recipe_data = json.loads(response.choices[0].message.content)
        return recipe_data["recipes"][0]
    except Exception as e:
        st.error(f"Error generating alternative recipe: {str(e)}")
        return None


def get_weekly_meal_plan(preferences, num_meals):
    prompt = generate_recipe_prompt(preferences, meal_count=num_meals)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o mini model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        recipe_data = json.loads(response.choices[0].message.content)
        recipes = recipe_data["recipes"]
        # Ensure we get exactly the number of meals requested
        while len(recipes) < num_meals:
            additional_recipes = get_weekly_meal_plan(preferences, num_meals - len(recipes))
            if additional_recipes:
                recipes.extend(additional_recipes)
        return recipes[:num_meals]
    except Exception as e:
        st.error(f"Error generating weekly meal plan: {str(e)}")
        return None