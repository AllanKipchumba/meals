import json
import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini API with flexible API key handling
def get_gemini_client():
    # Check if we already have a configured client in session state
    if 'gemini_configured' in st.session_state and st.session_state.gemini_configured:
        return True
    
    # Try to get API key from environment variables first
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Check if we have an API key in session state (user provided)
    if not api_key and 'api_key' in st.session_state and st.session_state.api_key:
        api_key = st.session_state.api_key
    
    if not api_key:
        # Silent error - don't show anything in UI
        return False
    
    try:
        # Configure the Gemini API with the key
        genai.configure(api_key=api_key)
        
        # Test that the API is working by listing available models
        try:
            models = genai.list_models()
            model_names = [model.name for model in models]
            st.session_state.available_models = model_names
            st.session_state.gemini_configured = True
            return True
        except Exception as e:
            # Silent failure
            return False
except Exception as e:
        # Silent failure
        return False

# Generate text using Gemini
def generate_gemini_response(prompt, model="gemini-1.0-pro"):
    if not get_gemini_client():
        st.error("API key configuration issue. Check that your GEMINI_API_KEY is set in the .env file.")
        return None
    
    # Try to use an available model if the requested one isn't available
    if hasattr(st.session_state, 'available_models'):
        available_models = st.session_state.available_models
        if model not in available_models and available_models:
            for possible_model in ["gemini-1.0-pro", "gemini-pro", "gemini-1.5-flash"]:
                if any(m.endswith(possible_model) for m in available_models):
                    model = next(m for m in available_models if m.endswith(possible_model))
                    break
    
    try:
        generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 4096,
        }
        
        # Show a spinner while generating content
        with st.spinner(f"Generating meal plan..."):
            model = genai.GenerativeModel(model_name=model, 
                                        generation_config=generation_config)
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # Check if we have a valid response
            if not hasattr(response, 'text') or not response.text:
                st.error("Received an empty response from Gemini API")
                if hasattr(response, 'prompt_feedback'):
                    st.error(f"Prompt feedback: {response.prompt_feedback}")
                return None
            
            # Debug: store the raw response but don't display
            st.session_state.last_gemini_response = response.text
            
            # Find and extract the JSON part from the response
            text = response.text.strip()
            
            # Look for JSON object between { and }
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                # Store the extracted JSON string but don't display
                st.session_state.extracted_json = json_str
                return json_str
            else:
                st.error("Could not parse the recipe data")
                return None
    except Exception as e:
        st.error(f"Error generating content: {str(e)}")
        return None

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

    base_prompt = f"You are a professional chef and nutrition expert. I need you to {meal_prompt} ({recipe_count}) {cuisine_prompt} based on these preferences:\n"
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

I need your response to be a valid, parsable JSON object ONLY, with no other text before or after. The JSON must follow this exact format:"""

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
    
    response_text = generate_gemini_response(prompt)
    if not response_text:
        return None
    
    try:
        recipe_data = json.loads(response_text)
        return recipe_data["recipes"][0]
    except Exception as e:
        st.error(f"Error parsing recipe data: {str(e)}")
        # Show the raw response for debugging
        if 'last_gemini_response' in st.session_state:
            with st.expander("Show raw API response"):
                st.text(st.session_state.last_gemini_response)
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
    
    response_text = generate_gemini_response(prompt)
    if not response_text:
        return None
    
    try:
        recipe_data = json.loads(response_text)
        return recipe_data["recipes"][0]
    except Exception as e:
        st.error(f"Error parsing alternative recipe data: {str(e)}")
        # Show the raw response for debugging
        if 'last_gemini_response' in st.session_state:
            with st.expander("Show raw API response"):
                st.text(st.session_state.last_gemini_response)
        return None


def get_weekly_meal_plan(preferences, num_meals):
    prompt = generate_recipe_prompt(preferences, meal_count=num_meals)
    
    response_text = generate_gemini_response(prompt)
    if not response_text:
        return None
    
    try:
        recipe_data = json.loads(response_text)
        recipes = recipe_data["recipes"]
        # Ensure we get exactly the number of meals requested
        while len(recipes) < num_meals:
            additional_recipes = get_weekly_meal_plan(preferences, num_meals - len(recipes))
            if additional_recipes:
                recipes.extend(additional_recipes)
        return recipes[:num_meals]
    except Exception as e:
        st.error(f"Error generating weekly meal plan: {str(e)}")
        # Show the raw response for debugging
        if 'last_gemini_response' in st.session_state:
            with st.expander("Show raw API response"):
                st.text(st.session_state.last_gemini_response)
        if 'extracted_json' in st.session_state:
            with st.expander("Show extracted JSON"):
                st.text(st.session_state.extracted_json)
        return None