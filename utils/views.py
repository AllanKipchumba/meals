import streamlit as st
from .recipe_generator import  get_alternative_recipe, get_weekly_meal_plan
from .recipe_utils import adjust_ingredient_quantity, generate_shopping_list
from database.queries import Database

# Corrected import based on functions available in subscription.py
from utils.subscription import handle_subscription_checkout, check_subscription_status

def format_recipe_for_printing(recipe):
    """Formats a recipe into a printable text format."""
    text = f"{recipe['name']}\n\n"
    text += "**Cooking Time:** " + str(recipe['cooking_time']) + " mins\n"
    text += "**Calories:** " + str(recipe['calories']) + "\n"
    text += "**Difficulty:** " + recipe['difficulty'] + "\n\n"
    text += "**Ingredients:**\n"
    for ingredient in recipe["ingredients"]:
        text += f"• {ingredient}\n"
    text += "\n**Instructions:**\n"
    for i, instruction in enumerate(recipe["instructions"], 1):
        text += f"{i}. {instruction}\n"
    return text


def display_all_weekend_prep(recipes, recipe_type="recipe"):
    """Display consolidated weekend prep instructions for all recipes."""
    st.header("📅 Weekend Meal Prep Instructions")
    st.write(
        "Complete these preparation tasks during your weekend cooking session:"
    )

    # Prepare text for download
    prep_text = "📅 Weekend Meal Prep Instructions\n\n"

    for i, recipe in enumerate(recipes, 1):
        if "weekend_prep" in recipe:
            st.subheader(f"{recipe['name']}")
            prep_text += f"\n{recipe['name']}\n"
            for step in recipe["weekend_prep"]:
                st.write(f"• {step}")
                prep_text += f"• {step}\n"
        st.divider()
        prep_text += "\n"

    # Add download button
    col1, col2 = st.columns(2)
    with col1:
        if st.download_button(label="📥 Download Prep Instructions",
                              data=prep_text,
                              file_name="weekend_prep_instructions.txt",
                              mime="text/plain",
                              key=f"download_prep_{recipe_type}"):
            st.success("Weekend prep instructions downloaded!")
    with col2:
        if st.button("↩️ Back to Recipes",
                     key=f"back_from_prep_{recipe_type}"):
            st.session_state.show_weekend_prep = False
            st.session_state.show_all_recipes = False
            st.session_state.show_shopping_list = False
            st.rerun()


def display_all_recipes(recipes, recipe_type=""):
    """Display all recipes in a printable format."""
    st.header("📖 All Recipes")

    for i, recipe in enumerate(recipes):
        # Create a container for each recipe
        with st.container():
            # Recipe header with favorite button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(recipe["name"])
            with col2:
                if st.session_state.get('logged_in'):
                    db = Database()
                    recipe_id = recipe.get('id')
                    if recipe_id:
                        try:
                            is_favorite = db.is_recipe_favorited(st.session_state['user']['id'], recipe_id)
                            favorite_text = "★ Remove from Favorites" if is_favorite else "⭐ Add to Favorites"
                            if st.button(favorite_text, key=f"favorite_all_{recipe_id}_{i}", use_container_width=True):
                                if is_favorite:
                                    db.remove_favourite_recipe(st.session_state['user']['id'], recipe_id)
                                    st.success("Recipe removed from favorites!")
                                else:
                                    db.add_favoureted_recipe(st.session_state['user']['id'], recipe_id)
                                    st.success("Recipe added to favorites!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error handling favorites: {str(e)}")

            # Basic Info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cooking Time", f"{recipe['cooking_time']} mins")
            with col2:
                st.metric("Calories", recipe["calories"])
            with col3:
                st.metric("Difficulty", recipe["difficulty"])

            # Ingredients
            st.write("**Ingredients:**")
            for ingredient in recipe["ingredients"]:
                st.write(f"• {ingredient}")

            # Instructions
            st.write("**Instructions:**")
            for i, instruction in enumerate(recipe["instructions"], 1):
                st.write(f"{i}. {instruction}")

            st.divider()

    if st.button("↩️ Back to Recipes", key=f"back_from_all_recipes_{recipe_type}"):
        st.session_state.show_weekend_prep = False
        st.session_state.show_all_recipes = False
        st.session_state.show_shopping_list = False
        st.rerun()


def display_recipe(recipe, index=None):
    """Display a single recipe with all its details"""
    if not recipe:
        st.error("No recipe data available")
        return

    # Create a container for the recipe header with favorite button
    header_container = st.container()
    with header_container:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {recipe.get('name', 'Unnamed Recipe')}")
        with col2:
            if st.session_state.get('logged_in'):
                db = Database()
                # Get recipe ID - handle both dictionary and object cases
                recipe_id = recipe.get('id')
                if recipe_id:
                    try:
                        # Check if recipe is already favorited
                        is_favorite = db.is_recipe_favorited(st.session_state['user']['id'], recipe_id)
                        favorite_text = "★ Remove from Favorites" if is_favorite else "⭐ Add to Favorites"
                        button_key = f"favorite_{recipe_id}_{index}" if index else f"favorite_{recipe_id}"
                        if st.button(favorite_text, key=button_key, use_container_width=True):
                            if is_favorite:
                                db.remove_favourite_recipe(st.session_state['user']['id'], recipe_id)
                                st.success("Recipe removed from favorites!")
                            else:
                                db.add_favoureted_recipe(st.session_state['user']['id'], recipe_id)
                                st.success("Recipe added to favorites!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error handling favorites: {str(e)}")
    
    # Display recipe details
    st.markdown("#### Ingredients")
    for ingredient in recipe.get('ingredients', []):
        st.markdown(f"- {ingredient}")
    
    st.markdown("#### Instructions")
    for i, instruction in enumerate(recipe.get('instructions', []), 1):
        st.markdown(f"{i}. {instruction}")
    
    # Display nutritional information
    st.markdown("#### Nutritional Information")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calories", recipe.get('calories', 0))
    with col2:
        st.metric("Protein", f"{recipe.get('protein', 0)}g")
    with col3:
        st.metric("Carbs", f"{recipe.get('carbs', 0)}g")
    with col4:
        st.metric("Fat", f"{recipe.get('fat', 0)}g")
    
    # Display additional information
    st.markdown("#### Additional Information")
    st.markdown(f"- **Difficulty**: {recipe.get('difficulty', 'Not specified')}")
    st.markdown(f"- **Cooking Time**: {recipe.get('cooking_time', 0)} minutes")
    st.markdown(f"- **Prep Time**: {recipe.get('prep_time', 0)} minutes")
    st.markdown(f"- **Servings**: {recipe.get('servings', 1)}")
    
    if recipe.get('dietary_info'):
        st.markdown("#### Dietary Information")
        for info in recipe['dietary_info']:
            st.markdown(f"- {info}")
    
    if recipe.get('weekend_prep'):
        st.markdown("#### Weekend Prep")
        for prep in recipe['weekend_prep']:
            st.markdown(f"- {prep}")

def display_favorite_recipes():
    """Display all favorite recipes for the current user"""
    if not st.session_state.get('logged_in'):
        st.error("Please log in to view your favorite recipes.")
        return
    
    db = Database()
    user_id = st.session_state['user']['id']
    
    # Get favorite recipes
    favorites = db.get_favorite_recipes(user_id)
    
    if not favorites:
        st.info("You haven't added any recipes to your favorites yet.")
        return
    
    st.markdown("### Your Favorite Recipes")
    
    # Display recipes in a grid
    cols = st.columns(3)
    for i, recipe in enumerate(favorites):
        with cols[i % 3]:
            with st.expander(recipe['name']):
                display_recipe(recipe)

def display_subscription_page(user_id: str):
    """Display subscription plans and handle subscription management"""
    st.title("Subscription Plans")

    # Check if user is logged in
    if not user_id:
        st.warning("Please log in to view subscription plans")
        return

    # Get subscription plans
    db = Database()
    plans = db.get_subscription_plans()

    if not plans:
        st.error("No subscription plans available")
        return

    # Check user's current subscription
    subscription = db.get_user_subscription(user_id)
    if subscription:
        st.success(f"You are currently subscribed to the {subscription['plan_name']} plan")
        if st.button("Manage Subscription"):
            # TODO: Implement subscription management
            st.info("Subscription management coming soon!")

    # Display subscription plans
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Plan")
        st.write("$20.00 per month")
        st.write("Features:")
        st.write("- Unlimited meal plan generation")
        st.write("- Access to all features")
        st.write("- Priority support")

        if st.button("Subscribe Monthly", key="monthly"):
            # Call the function to handle checkout; it opens the URL directly
            handle_subscription_checkout()
            # Note: The original function expected a price_id, the new one uses env var.
            # This might need further adjustment depending on desired behavior.

    with col2:
        st.subheader("Annual Plan")
        st.write("$90.00 per year (25% savings)")
        st.write("Features:")
        st.write("- Unlimited meal plan generation")
        st.write("- Access to all features")
        st.write("- Priority support")
        st.write("- 25% discount")

        if st.button("Subscribe Annual", key="annual"):
            # Call the function to handle checkout; it opens the URL directly
            handle_subscription_checkout()
            # Note: The original function expected a price_id, the new one uses env var.
            # This might need further adjustment depending on desired behavior.

    st.markdown("---")
    st.info("All users can generate up to 3 meal plans. Subscribe to unlock unlimited meal plan generation!")

    # Check subscription status (handles session_id internally from query params)
    check_subscription_status()

def display_user_plan_page(user_id: str):
    """Display user's current subscription plan and handle subscription management"""
    st.title("Your Subscription Plan")

    db = Database()
    plan_info = db.get_user_subscription_plan(user_id)

    if plan_info["plan_name"]:
        st.subheader(f"Current Plan: {plan_info['plan_name']}")
        if plan_info["is_active"]:
            st.success("Your subscription is active 🎉")
        else:
            st.warning("Your subscription is inactive or expired.")
            # if st.button("Renew Subscription"):
            #     plans = db.get_all_subscription_plans()
            #     for plan in plans:
            #         st.write(f"**{plan['name']}** - ${plan['price_amount']} / {plan['interval']}")
            #         if st.button(f"Subscribe to {plan['name']}", key=plan['id']):
            #             session_url = create_checkout_session(user_id, plan['price_id'])
            #             if session_url:
            #                 st.success("Redirecting to checkout...")
            #                 st.markdown(f"[Click here to continue to Stripe Checkout]({session_url})", unsafe_allow_html=True)
            #             else:
            #                 st.error("Failed to create checkout session. Please try again.")
    else:
        st.warning("You do not have an active subscription plan.")
        st.write("Choose a subscription plan below to get started:")

        # plans = db.get_all_subscription_plans()
        # for plan in plans:
        #     st.write(f"**{plan['name']}** - ${plan['price_amount']} / {plan['interval']}")
        #     st.write(plan['description'])
        #     for feature in plan['features']:
        #         st.markdown(f"- {feature}")
        #     if st.button(f"Subscribe to {plan['name']}", key=plan['id']):
        #         session_url = create_checkout_session(user_id, plan['price_id'])
        #         if session_url:
        #             st.success("Redirecting to checkout...")
        #             st.markdown(f"[Click here to continue to Stripe Checkout]({session_url})", unsafe_allow_html=True)
        #         else:
        #             st.error("Failed to create checkout session. Please try again.")


def display_recipe_generator():
    """Display meal plan generation form and handle generation"""
    st.title("Generate Meal Plan")
    
    # # Check if user is logged in
    # if not st.session_state.get('user_id'):
    #     st.warning("Please log in to generate meal plans")
    #     return
    
    # # Check subscription status and meal plan limit
    # db = Database()
    # subscription = db.get_user_subscription(st.session_state.user_id)
    # total_recipes = db.get_total_recipe_count(st.session_state.user_id)
    
    # # Show remaining meal plans for non-subscribers
    # if not subscription:
    #     remaining_recipes = max(0, 3 - total_recipes)
    #     if remaining_recipes == 0:
    #         st.error("You've reached your limit of 3 meal plans. Please subscribe to generate unlimited meal plans!")
    #         if st.button("View Subscription Plans"):
    #             st.session_state.page = "Subscription"
    #             st.rerun()
    #         return
    #     st.info(f"You can generate {remaining_recipes} more meal plan{'s' if remaining_recipes > 1 else ''}. Subscribe for unlimited access!")
    
    # Meal plan generation form
    with st.form("recipe_form"):
        st.subheader("Meal Plan Preferences")
        
        # Dietary preferences
        dietary_preferences = st.multiselect(
            "Dietary Preferences",
            ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Paleo"]
        )
        
        # Allergies
        allergies = st.multiselect(
            "Allergies",
            ["Peanuts", "Tree Nuts", "Shellfish", "Fish", "Soy", "Eggs", "Milk", "Wheat"]
        )
        
        # Nutritional goals
        col1, col2, col3 = st.columns(3)
        with col1:
            calorie_goal = st.number_input("Daily Calorie Goal", min_value=0, value=2000)
        with col2:
            protein_goal = st.number_input("Daily Protein Goal (g)", min_value=0, value=50)
        with col3:
            carbs_goal = st.number_input("Daily Carbs Goal (g)", min_value=0, value=200)
        
        # Meal plan preferences
        col1, col2 = st.columns(2)
        with col1:
            cooking_time = st.selectbox(
                "Maximum Cooking Time per Meal",
                ["15 minutes", "30 minutes", "45 minutes", "1 hour", "1.5 hours", "2+ hours"]
            )
        with col2:
            difficulty = st.selectbox(
                "Difficulty Level",
                ["Easy", "Medium", "Hard"]
            )
        
        # Generate button
        if st.form_submit_button("Generate Meal Plan"):
            # Check limit again before generating
            # if not subscription and total_recipes >= 3:
            #     st.error("You've reached your limit of 3 meal plans. Please subscribe to generate unlimited meal plans!")
            #     if st.button("View Subscription Plans", key="subscribe_after_limit"):
            #         st.session_state.page = "Subscription"
            #         st.rerun()
            #     return
            
            # Generate meal plan
            recipe = generate_recipe(
                dietary_preferences=dietary_preferences,
                allergies=allergies,
                calorie_goal=calorie_goal,
                protein_goal=protein_goal,
                carbs_goal=carbs_goal,
                cooking_time=cooking_time,
                difficulty=difficulty
            )
            
            if recipe:
                # Save meal plan to database
                recipe_id = db.create_recipe(
                    user_id=st.session_state.user_id,
                    name=recipe['name'],
                    ingredients=recipe['ingredients'],
                    instructions=recipe['instructions'],
                    calories=recipe['calories'],
                    protein=recipe['protein'],
                    carbs=recipe['carbs'],
                    fat=recipe['fat'],
                    tags=recipe['tags'],
                    difficulty=recipe['difficulty'],
                    dietary_info=recipe['dietary_info'],
                    cooking_time=recipe['cooking_time'],
                    prep_time=recipe['prep_time'],
                    weekend_prep=recipe['weekend_prep'],
                    servings=recipe['servings']
                )
                
                # Display meal plan
                display_recipe(recipe_id)
            else:
                st.error("Failed to generate meal plan. Please try again.")
