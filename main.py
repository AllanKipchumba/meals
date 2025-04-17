import os
from dotenv import load_dotenv

# Load environment variables before any imports that use them
load_dotenv()

import streamlit as st
from utils.recipe_generator import get_weekly_meal_plan
from utils.shopping_list import generate_shopping_list
from utils.views import display_all_recipes,display_all_weekend_prep,display_recipe,format_recipe_for_printing, display_favorite_recipes, display_subscription_page, display_user_plan_page
from utils.auth import login_user, handle_callback,check_authentication
from database.queries import Database
from database.init_db import init_database
# Removed import for non-existent/replaced functions: init_subscription_plans, handle_checkout_session

import time
from utils.subscription import handle_subscription_checkout

# Add this constant before the show_subscription_status function
FREE_MONTHLY_LIMIT = 4

# Add to main.py sidebar
def show_subscription_status():
    user_id = st.session_state['user']['id']
    db = Database()
    
    monthly_count = db.get_monthly_generations(user_id)
    subscription = db.get_user_subscription(user_id)
    
    with st.sidebar:
        # Add user info and logout button at the top
        if 'user' in st.session_state:
            st.write(f"👤 {st.session_state['user']['username']}")
            if st.button("Logout", key="logout_button", type="secondary"):
                from utils.auth import logout_user
                logout_user()
        
        # Existing subscription status code
        if subscription:
            st.success("Premium Member")
            st.write("Generate Unlimited meal plans")
        else:
            st.info(f"Free Plan: {monthly_count}/{FREE_MONTHLY_LIMIT} generations this month")
            if monthly_count >= FREE_MONTHLY_LIMIT:
                if st.button("Upgrade to Premium"):
                    handle_subscription_checkout()

def main():
    # INITIALIZE DATABASE
    init_database()   
    
    # Add this near the top of your main function
    from utils.subscription import check_subscription_status, check_generation_limits, show_upgrade_modal
    check_subscription_status()
    
    if 'auth_checked' not in st.session_state:
        st.session_state['auth_checked'] = False
    
    # Process OAuth callback if present
    if "state" in st.query_params:
        st.set_page_config(
            page_title="Authentication",
            initial_sidebar_state="collapsed"
        )
        st.subheader("Authentication Callback")
        st.write("Processing your login...")
        handle_callback()
        return    
    
    center_spinner_css = """
        <style>
        /* Hide the default Streamlit expander header */
        .streamlit-expanderHeader {
            display: none;
        }
        
        /* Custom CSS to center the spinner */
        .stSpinner {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .stSpinner > div {
            margin: 0;  
            padding: 0;
            width:100%
            display: flex;
            justify-content: center;
        }
        </style>
    """
    st.markdown(center_spinner_css, unsafe_allow_html=True)

    # Removed redundant status check block, as check_subscription_status handles this
    
    if 'auth_checked' not in st.session_state or not st.session_state['auth_checked']:
        with st.spinner(""):
            is_authenticated = check_authentication()
            st.session_state['auth_checked'] = True
            st.session_state['is_authenticated'] = is_authenticated
    else:
        is_authenticated = check_authentication()
        st.session_state['is_authenticated'] = is_authenticated
    
    # Show appropriate content based on authentication status
    if not st.session_state['is_authenticated']:
        login_user()
    else:
        # Initialize session state variables
        if 'weekly_recipes' not in st.session_state:
            st.session_state.weekly_recipes = {}
        if 'dinner_recipes' not in st.session_state:
            st.session_state.dinner_recipes = []
        if 'breakfast_recipes' not in st.session_state:
            st.session_state.breakfast_recipes = []
        if 'show_weekend_prep' not in st.session_state:
            st.session_state.show_weekend_prep = False
        if 'show_all_recipes' not in st.session_state:
            st.session_state.show_all_recipes = False
        if 'show_shopping_list' not in st.session_state:
            st.session_state.show_shopping_list = False
        if 'preferences' not in st.session_state:
            st.session_state.preferences = {}
        if 'past_recipes' not in st.session_state:
            st.session_state.past_recipes = []  # Initialize past recipes
        if 'show_upgrade_modal' not in st.session_state:
            st.session_state.show_upgrade_modal = False # Initialize flag for upgrade modal

        st.title("Personal Meal Planner")
        st.subheader("Tell us about your preferences")

        show_subscription_status()

        with st.form("user_preferences"):
            # Number of meals per week
            st.subheader("Meal Plan Duration")
            col1, col2 = st.columns(2)
            with col1:
                num_dinners = st.number_input(
                    "Number of dinners to generate:",
                    min_value=1,
                    max_value=7,
                    value=4,
                    step=1,
                    help=
                    "Choose how many different dinners you want in your plan (max 7)"
                )
            with col2:
                num_breakfasts = st.number_input(
                    "Number of breakfasts to generate:",
                    min_value=0,
                    max_value=7,
                    value=4,
                    step=1,
                    help=
                    "Choose how many different breakfasts you want in your plan (max 7)"
                )

            # Dietary Restrictions
            st.subheader("Dietary Preferences")
            st.write("Select any dietary restrictions that apply:")

            # Create columns for checkboxes to make the layout more compact
            col1, col2 = st.columns(2)

            with col1:
                vegetarian = st.checkbox("Vegetarian")
                vegan = st.checkbox("Vegan")

            with col2:
                gluten_free = st.checkbox("Gluten-Free")
                dairy_free = st.checkbox("Dairy-Free")

            # Collect all selected dietary restrictions
            dietary_restrictions = []
            if vegetarian: dietary_restrictions.append("Vegetarian")
            if vegan: dietary_restrictions.append("Vegan")
            if gluten_free: dietary_restrictions.append("Gluten-Free")
            if dairy_free: dietary_restrictions.append("Dairy-Free")

            # Cooking Time
            st.subheader("Cooking Time")
            cooking_time = st.slider("Maximum cooking time (minutes):",
                                    min_value=15,
                                    max_value=120,
                                    value=30,
                                    step=15)

            # Cooking Skill Level
            st.subheader("Cooking Experience")
            skill_level = st.select_slider(
                "What's your cooking skill level?",
                options=["Beginner", "Intermediate", "Advanced"],
                value="Intermediate")

            # Cuisine Preference
            st.subheader("Cuisine Preference")
            cuisine_preference = st.selectbox(
                "What type of cuisine would you prefer?",
                options=[
                    "Any", "Italian", "Mexican", "Chinese", "Japanese", "Indian",
                    "Mediterranean", "French", "Thai", "American"
                ],
                index=0,
                help="Select your preferred cuisine type for the recipes")

            # Dinner Nutritional Goals
            st.subheader("Dinner Nutritional Goals")
            col1, col2 = st.columns(2)
            with col1:
                dinner_min_calories = st.number_input("Minimum dinner calories:",
                                                    min_value=200,
                                                    max_value=1500,
                                                    value=400,
                                                    step=50)
                dinner_min_protein = st.number_input("Minimum dinner protein (g):",
                                                    min_value=0,
                                                    max_value=200,
                                                    value=35,
                                                    step=5)
                dinner_max_total_fat = st.number_input(
                    "Maximum dinner total fat (g):",
                    min_value=0,
                    max_value=100,
                    value=30,
                    step=5)
            with col2:
                dinner_max_calories = st.number_input("Maximum dinner calories:",
                                                    min_value=300,
                                                    max_value=2000,
                                                    value=600,
                                                    step=50)
                dinner_max_carbs = st.number_input("Maximum dinner carbs (g):",
                                                min_value=0,
                                                max_value=300,
                                                value=40,
                                                step=5)
                dinner_max_saturated_fat = st.number_input(
                    "Maximum dinner saturated fat (g):",
                    min_value=0,
                    max_value=50,
                    value=10,
                    step=2)

            # Breakfast Nutritional Goals
            st.subheader("Breakfast Nutritional Goals")
            col1, col2 = st.columns(2)
            with col1:
                breakfast_min_calories = st.number_input(
                    "Minimum breakfast calories:",
                    min_value=200,
                    max_value=1500,
                    value=300,
                    step=50)
                breakfast_min_protein = st.number_input(
                    "Minimum breakfast protein (g):",
                    min_value=0,
                    max_value=200,
                    value=20,
                    step=5)
                breakfast_max_total_fat = st.number_input(
                    "Maximum breakfast total fat (g):",
                    min_value=0,
                    max_value=100,
                    value=20,
                    step=5)
            with col2:
                breakfast_max_calories = st.number_input(
                    "Maximum breakfast calories:",
                    min_value=300,
                    max_value=2000,
                    value=500,
                    step=50)
                breakfast_max_carbs = st.number_input(
                    "Maximum breakfast carbs (g):",
                    min_value=0,
                    max_value=300,
                    value=50,
                    step=5)
                breakfast_max_saturated_fat = st.number_input(
                    "Maximum breakfast saturated fat (g):",
                    min_value=0,
                    max_value=50,
                    value=8,
                    step=2)

            # Additional Preferences
            st.subheader("Additional Preferences")
            exclude_ingredients = st.text_input(
                "Any ingredients to avoid? (comma-separated)",
                placeholder="e.g., mushrooms, olives, seafood")

            # Submit Button
            submitted = st.form_submit_button("Generate Meal Plan")

            if submitted:
                user_id = st.session_state['user']['id']

                # Check generation limits
                if not check_generation_limits(user_id):
                    st.session_state.show_upgrade_modal = True # Set flag instead of calling directly
                    st.rerun() # Rerun to show modal outside the form

                # Continue with meal plan generation (will only run if limit not reached)
                dinner_preferences = {
                    "dietary_restrictions":
                    dietary_restrictions,
                    "cooking_time":
                    cooking_time,
                    "skill_level":
                    skill_level,
                    "cuisine_preference":
                    cuisine_preference,
                    "min_calories":
                    dinner_min_calories,
                    "max_calories":
                    dinner_max_calories,
                    "min_protein":
                    dinner_min_protein,
                    "max_carbs":
                    dinner_max_carbs,
                    "max_total_fat":
                    dinner_max_total_fat,
                    "max_saturated_fat":
                    dinner_max_saturated_fat,
                    "exclude_ingredients": [
                        i.strip() for i in exclude_ingredients.split(",")
                        if i.strip()
                    ],
                    "meal_type":
                    "dinner"
                }

                breakfast_preferences = {
                    "dietary_restrictions":
                    dietary_restrictions,
                    "cooking_time":
                    cooking_time,
                    "skill_level":
                    skill_level,
                    "cuisine_preference":
                    cuisine_preference,
                    "min_calories":
                    breakfast_min_calories,
                    "max_calories":
                    breakfast_max_calories,
                    "min_protein":
                    breakfast_min_protein,
                    "max_carbs":
                    breakfast_max_carbs,
                    "max_total_fat":
                    breakfast_max_total_fat,
                    "max_saturated_fat":
                    breakfast_max_saturated_fat,
                    "exclude_ingredients": [
                        i.strip() for i in exclude_ingredients.split(",")
                        if i.strip()
                    ],
                    "meal_type":
                    "breakfast"
                }

                st.session_state['dinner_preferences'] = dinner_preferences
                st.session_state['breakfast_preferences'] = breakfast_preferences

                dinner_recipes = []
                breakfast_recipes = []

                # Generate dinner recipes
                if num_dinners > 0:
                    dinner_recipes = get_weekly_meal_plan(
                        st.session_state['dinner_preferences'], num_dinners)

                # Generate breakfast recipes
                if num_breakfasts > 0:
                    breakfast_recipes = get_weekly_meal_plan(
                        st.session_state['breakfast_preferences'], num_breakfasts)
                
                # After successful generation, log it
                db = Database()
                db.log_meal_generation(user_id)
                
                if dinner_recipes or breakfast_recipes:
                    st.session_state['dinner_recipes'] = dinner_recipes
                    st.session_state['breakfast_recipes'] = breakfast_recipes
                    st.rerun()

        # Check if we need to show the upgrade modal (outside the form)
        if st.session_state.get('show_upgrade_modal', False):
            show_upgrade_modal()
            st.session_state.show_upgrade_modal = False # Reset the flag after showing

        # Display recipes based on whether it's a weekly plan or single recipe
        elif 'dinner_recipes' in st.session_state or 'breakfast_recipes' in st.session_state: # Use elif to avoid showing recipes if modal is shown
            tabs = st.tabs(["Your Weekly Meal Plan", "Past Recipes"])
            with tabs[0]:
                st.header("Your Weekly Meal Plan")

                # Display consolidated views or individual recipes
                if st.session_state.get('show_weekend_prep', False):
                    if st.session_state.get('dinner_recipes'):
                        st.subheader("Dinner Prep")
                        display_all_weekend_prep(st.session_state.dinner_recipes,
                                                "dinner")
                    if st.session_state.get('breakfast_recipes'):
                        st.subheader("Breakfast Prep")
                        display_all_weekend_prep(
                            st.session_state.breakfast_recipes, "breakfast")
                elif st.session_state.get('show_all_recipes', False):
                    if st.session_state.get('dinner_recipes'):
                        st.subheader("Dinner Recipes")
                        display_all_recipes(st.session_state.dinner_recipes,
                                            "dinner")
                    if st.session_state.get('breakfast_recipes'):
                        st.subheader("Breakfast Recipes")
                        display_all_recipes(st.session_state.breakfast_recipes,
                                            "breakfast")
                else:
                    # Display breakfast recipes
                    if st.session_state.get('breakfast_recipes'):
                        st.subheader("Breakfast Recipes")
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            # Master download for all breakfast recipes
                            all_breakfast_text = "🍳 All Breakfast Recipes\n\n"
                            for i, recipe in enumerate(
                                    st.session_state.breakfast_recipes, 1):
                                all_breakfast_text += f"=== Breakfast {i} ===\n"
                                all_breakfast_text += format_recipe_for_printing(
                                    recipe) + "\n\n"

                            if st.download_button(
                                    label="📥 Download All Breakfasts",
                                    data=all_breakfast_text,
                                    file_name="all_breakfast_recipes.txt",
                                    mime="text/plain",
                                    key="download_all_breakfasts"):
                                st.success("All breakfast recipes downloaded!")

                        breakfast_tabs = st.tabs([
                            f"Breakfast {i+1}"
                            for i in range(len(st.session_state.breakfast_recipes))
                        ])
                        for i, (tab, recipe) in enumerate(
                                zip(breakfast_tabs,
                                    st.session_state.breakfast_recipes)):
                            with tab:
                                display_recipe(recipe, index=f"breakfast_{i}")
                                # Individual recipe download
                                if st.download_button(
                                        label="📥 Download This Recipe",
                                        data=format_recipe_for_printing(recipe),
                                        file_name=
                                        f"{recipe['name'].lower().replace(' ', '_')}.txt",
                                        mime="text/plain",
                                        key=f"download_breakfast_{i}"):
                                    st.success("Recipe downloaded!")

                    # Display dinner recipes
                    if st.session_state.get('dinner_recipes'):
                        st.subheader("Dinner Recipes")
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            # Master download for all dinner recipes
                            all_dinner_text = "🍽️ All Dinner Recipes\n\n"
                            for i, recipe in enumerate(
                                    st.session_state.dinner_recipes, 1):
                                all_dinner_text += f"=== Dinner {i} ===\n"
                                all_dinner_text += format_recipe_for_printing(
                                    recipe) + "\n\n"

                            if st.download_button(
                                    label="📥 Download All Dinners",
                                    data=all_dinner_text,
                                    file_name="all_dinner_recipes.txt",
                                    mime="text/plain",
                                    key="download_all_dinners"):
                                st.success("All dinner recipes downloaded!")

                        dinner_tabs = st.tabs([
                            f"Dinner {i+1}"
                            for i in range(len(st.session_state.dinner_recipes))
                        ])
                        for i, (tab, recipe) in enumerate(
                                zip(dinner_tabs, st.session_state.dinner_recipes)):
                            with tab:
                                display_recipe(recipe, index=f"dinner_{i}")
                                # Individual recipe download
                                if st.download_button(
                                        label="📥 Download This Recipe",
                                        data=format_recipe_for_printing(recipe),
                                        file_name=
                                        f"{recipe['name'].lower().replace(' ', '_')}.txt",
                                        mime="text/plain",
                                        key=f"download_dinner_{i}"):
                                    st.success("Recipe downloaded!")

                # Add buttons at the bottom
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📅 Weekend Meal Prep"):
                        st.session_state.show_weekend_prep = True
                        st.session_state.show_all_recipes = False
                        st.rerun()
                with col2:
                    if st.button("📖 All Recipes"):
                        st.session_state.show_weekend_prep = False
                        st.session_state.show_all_recipes = True
                        st.rerun()
                with col3:
                    if st.button("🛒 Generate Shopping List"):
                        # Combine breakfast and dinner recipes
                        all_recipes = []
                        serving_multipliers = []

                        # Add breakfast recipes
                        if st.session_state.get('breakfast_recipes'):
                            all_recipes.extend(st.session_state.breakfast_recipes)
                            serving_multipliers.extend([
                                st.session_state.get(f"serving_breakfast_{i}", 1)
                                for i in range(
                                    len(st.session_state.breakfast_recipes))
                            ])

                        # Add dinner recipes
                        if st.session_state.get('dinner_recipes'):
                            all_recipes.extend(st.session_state.dinner_recipes)
                            serving_multipliers.extend([
                                st.session_state.get(f"serving_dinner_{i}", 1) for
                                i in range(len(st.session_state.dinner_recipes))
                            ])

                        if all_recipes:
                            st.session_state.shopping_list = generate_shopping_list(
                                all_recipes, serving_multipliers)
                            st.session_state.show_shopping_list = True
                            st.rerun()

                # Display shopping list if it exists in session state
                if st.session_state.get(
                        'show_shopping_list',
                        False) and 'shopping_list' in st.session_state:
                    with st.expander("Shopping List", expanded=True):
                        st.subheader("🛒 Your Shopping List")

                        # Initialize have_already and need_to_buy in session state
                        if 'have_already' not in st.session_state:
                            st.session_state.have_already = set()

                        current_category = None
                        need_to_buy = []
                        have_already = []

                        for item in st.session_state.shopping_list:
                            if item.startswith('\n'):
                                # This is a category header
                                if current_category and (need_to_buy
                                                        or have_already):
                                    # Display the previous category's items
                                    if need_to_buy:
                                        st.markdown("**Need to Buy:**")
                                        for i in need_to_buy:
                                            st.write(f"• {i}")
                                    if have_already:
                                        st.markdown("**Have Already:**")
                                        for i in have_already:
                                            st.write(f"✓ {i}")

                                current_category = item.strip(':')
                                st.markdown(f"### {current_category}")
                                need_to_buy = []
                                have_already = []
                            else:
                                # This is an ingredient item
                                clean_item = item.replace('• ', '')
                                if st.checkbox(clean_item,
                                            key=f"check_{clean_item}",
                                            value=clean_item
                                            in st.session_state.have_already):
                                    st.session_state.have_already.add(clean_item)
                                    have_already.append(clean_item)
                                else:
                                    if clean_item in st.session_state.have_already:
                                        st.session_state.have_already.remove(
                                            clean_item)
                                    need_to_buy.append(clean_item)

                        # Display the last category's items
                        if current_category and (need_to_buy or have_already):
                            if need_to_buy:
                                st.markdown("**Need to Buy:**")
                                for i in need_to_buy:
                                    st.write(f"• {i}")
                            if have_already:
                                st.markdown("**Have Already:**")
                                for i in have_already:
                                    st.write(f"✓ {i}")

                        # Export options
                        st.divider()
                        # Create the Need to Buy list with categories
                        need_to_buy_by_category = {}
                        current_category = None

                        for item in st.session_state.shopping_list:
                            if item.startswith('\n'):
                                current_category = item.strip('\n:')
                                need_to_buy_by_category[current_category] = []
                            else:
                                clean_item = item.replace('• ', '')
                                if clean_item not in st.session_state.have_already:
                                    need_to_buy_by_category[
                                        current_category].append(clean_item)

                        # Create formatted text for the Need to Buy list
                        need_to_buy_text = "🛒 Shopping List - Need to Buy\n\n"
                        for category, items in need_to_buy_by_category.items():
                            if items:  # Only include categories with items
                                need_to_buy_text += f"{category}:\n"
                                need_to_buy_text += "\n".join(f"• {item}"
                                                            for item in items)
                                need_to_buy_text += "\n\n"

                        # Export options
                        st.divider()
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📋 Copy to Clipboard"):
                                st.write("Shopping list copied!")
                                st.code(need_to_buy_text, language=None)
                        with col2:
                            st.download_button(label="📥 Download List",
                                            data=need_to_buy_text,
                                            file_name="shopping_list.txt",
                                            mime="text/plain")

                        # Show Need to Buy list in a tabbed view
                        if st.button("🔍 View Need to Buy List"):
                            st.markdown("## 🛒 Need to Buy Items")
                            for category, items in need_to_buy_by_category.items():
                                if items:
                                    st.markdown(f"### {category}")
                                    for item in items:
                                        st.write(f"• {item}")
                            st.divider()

                    if st.button("↩️ Back to Recipes", key="shopping_list_back"):
                        st.session_state.show_weekend_prep = False
                        st.session_state.show_all_recipes = False
                        st.session_state.show_shopping_list = False
                        st.rerun()

            with tabs[1]:

                def show_past_recipes():
                    st.header("Past Recipes")
                    if 'user' not in st.session_state:
                        st.warning("Please log in to view your past recipes")
                        return

                    db = Database()
                    past_recipes = db.get_recipes(
                        st.session_state['user']['id'])
                    if not past_recipes:
                        st.info(
                            "No past recipes found. Generate some meal plans to see your history!"
                        )
                        return

                    for recipe in past_recipes:
                        with st.expander(
                                f"{recipe['name']} (Made on: {recipe['created_at'].strftime('%Y-%m-%d')})"
                        ):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(
                                    "**Description:**",
                                    recipe.get('description',
                                            'No description available'))
                                st.write("**Cooking Time:**",
                                        recipe.get('cooking_time', 'N/A'),
                                        "minutes")
                                st.write("**Calories:**",
                                        recipe.get('calories', 'N/A'))
                            with col2:
                                # Display existing rating if any
                                current_rating = recipe.get('rating')
                                if current_rating:
                                    st.write("**Your Rating:**",
                                            "⭐" * int(current_rating))

                                # Allow rating update
                                new_rating = st.select_slider(
                                    "Rate this recipe",
                                    options=[1, 2, 3, 4, 5],
                                    value=int(current_rating)
                                    if current_rating else 3,
                                    key=f"rate_past_{recipe['id']}")

                                keep_recipe = st.checkbox(
                                    "Keep this recipe", key=f"keep_{recipe['id']}")

                                if st.button("Update",
                                            key=f"update_rating_{recipe['id']}"):
                                    db.add_rating(st.session_state['user']['id'],
                                                recipe['id'], new_rating, None)

                                    if(keep_recipe):
                                        db.add_favoureted_recipe(
                                            st.session_state['user']['id'],
                                            recipe['id'])
                                    else:
                                        db.remove_favourite_recipe(
                                            st.session_state['user']['id'],
                                            recipe['id'])
                                    st.success("Recipe preferences updated!")


                                    st.rerun()

                show_past_recipes()

            try:
                db = Database()

                # Save dinner recipes if they exist
                if st.session_state.get('dinner_recipes'):
                    for recipe in st.session_state['dinner_recipes']:
                        if not recipe or not isinstance(recipe, dict):
                            continue

                        try:
                            # Parse calories value
                            calories_str = recipe.get('calories', '0')
                            if isinstance(calories_str, str):
                                calories_str = calories_str.split()[0]  # Get the number part

                            db.create_recipe(
                                user_id=st.session_state['user'].get("id"),
                                name=recipe.get('name', ''),
                                ingredients=recipe.get('ingredients', []),
                                instructions=recipe.get('instructions', []),
                                calories=int(calories_str),
                                protein=float(recipe.get('macros', {}).get('protein', '0').split()[0]),
                                carbs=float(recipe.get('macros', {}).get('carbs', '0').split()[0]),
                                fat=float(recipe.get('macros', {}).get('total_fat', '0').split()[0]),
                                tags=recipe.get('tags', []),
                                difficulty=recipe.get('difficulty', 'medium'),
                                dietary_info=recipe.get('dietary_info', []),
                                cooking_time=int(recipe.get('cooking_time', '0').split()[0]),
                                prep_time=20,
                                weekend_prep=recipe.get('weekend_prep', []),
                                servings=recipe.get('servings', 4)
                            )
                        except Exception as e:
                            st.error(f"Error saving dinner recipe {recipe.get('name', '')}: {str(e)}")

                # Save breakfast recipes if they exist
                if st.session_state.get('breakfast_recipes'):
                    for recipe in st.session_state['breakfast_recipes']:
                        if not recipe or not isinstance(recipe, dict):
                            continue

                        try:
                            # Parse calories value
                            calories_str = recipe.get('calories', '0')
                            if isinstance(calories_str, str):
                                calories_str = calories_str.split()[0]  # Get the number part

                            db.create_recipe(
                                user_id=st.session_state['user'].get("id"),
                                name=recipe.get('name', ''),
                                ingredients=recipe.get('ingredients', []),
                                instructions=recipe.get('instructions', []),
                                calories=int(calories_str),
                                protein=float(recipe.get('macros', {}).get('protein', '0').split()[0]),
                                carbs=float(recipe.get('macros', {}).get('carbs', '0').split()[0]),
                                fat=float(recipe.get('macros', {}).get('total_fat', '0').split()[0]),
                                tags=recipe.get('tags', []),
                                difficulty=recipe.get('difficulty', 'medium'),
                                dietary_info=recipe.get('dietary_info', []),
                                cooking_time=int(recipe.get('cooking_time', '0').split()[0]),
                                prep_time=30,
                                weekend_prep=recipe.get('weekend_prep', []),
                                servings=recipe.get('servings', 4)
                            )
                        except Exception as e:
                            st.error(f"Error saving breakfast recipe {recipe.get('name', '')}: {str(e)}")
            except Exception as e:
                st.error(f"Error saving recipes to database: {str(e)}")
        elif 'current_recipe' in st.session_state:
            display_recipe(st.session_state.current_recipe)

            # Add Shopping List Generation Button for single recipe
            if st.button("Generate Shopping List"):
                serving_multiplier = st.session_state.get("serving", 1)
                st.session_state.shopping_list = generate_shopping_list(
                    [st.session_state.current_recipe], [serving_multiplier])
                st.session_state.show_shopping_list = True
                st.rerun()

            # Display shopping list if it exists in session state
            if st.session_state.get('show_shopping_list',
                                    False) and 'shopping_list' in st.session_state:
                with st.expander("Shopping List", expanded=True):
                    st.subheader("🛒 Your Shopping List")
                    for item in st.session_state.shopping_list:
                        st.write(f"• {item}")

        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Home", "Subscription"])

        if page == "Subscription":
            # Removed call to non-existent init_subscription_plans()
            user_id = st.session_state.get('user', {}).get('id')
            display_user_plan_page(user_id)
            display_subscription_page(user_id=user_id)



if __name__ == "__main__":
    main()
