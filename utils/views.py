import streamlit as st
from .recipe_generator import  get_alternative_recipe
from .recipe_utils import adjust_ingredient_quantity
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

    for recipe in recipes:
        st.subheader(recipe["name"])

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
    if st.button("↩️ Back to Recipes",
                 key=f"back_from_all_recipes_{recipe_type}"):
        st.session_state.show_weekend_prep = False
        st.session_state.show_all_recipes = False
        st.session_state.show_shopping_list = False
        st.rerun()


def display_recipe(recipe, index=None):
    if recipe:
        st.header(recipe["name"])

        # Add serving size adjustment
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cooking Time", f"{recipe['cooking_time']} mins")
        with col2:
            st.metric("Calories", recipe["calories"])
        with col3:
            st.metric("Difficulty", recipe["difficulty"])
        with col4:
            serving_multiplier = st.number_input(
                "Number of servings",
                min_value=1,
                value=1,
                key=f"serving_{index}" if index is not None else "serving")

        # Add download button for recipe
        if st.download_button(
                label="📥 Download Recipe",
                data=format_recipe_for_printing(recipe),
                file_name=f"{recipe['name'].lower().replace(' ', '_')}.txt",
                mime="text/plain"):
            st.success("Recipe downloaded!")

        # Display macro nutrients
        st.subheader("Macro Nutrients")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Protein", recipe["macros"]["protein"])
        with col2:
            st.metric("Carbs", recipe["macros"]["carbs"])
        with col3:
            st.metric("Total Fat", recipe["macros"]["total_fat"])
        with col4:
            st.metric("Saturated Fat", recipe["macros"]["saturated_fat"])

        # Display dietary information
        st.subheader("Dietary Information")
        st.write(", ".join(recipe["dietary_info"]))

        # Display ingredients with adjusted quantities
        st.subheader("Ingredients")
        for ingredient in recipe["ingredients"]:
            adjusted_ingredient = adjust_ingredient_quantity(
                ingredient, serving_multiplier)
            st.write(f"• {adjusted_ingredient}")

        # Display weekend prep instructions
        if "weekend_prep" in recipe:
            with st.expander("📅 Weekend Prep Instructions", expanded=True):
                st.write(
                    "Complete these steps during your weekend prep session:")
                for i, prep_step in enumerate(recipe["weekend_prep"], 1):
                    st.write(f"{i}. {prep_step}")

        # Display weekday cooking instructions
        if "weekday_cooking" in recipe:
            with st.expander("🕒 Weekday Cooking Steps", expanded=True):
                st.write("Quick steps to finish the dish during the week:")
                for i, step in enumerate(recipe["weekday_cooking"], 1):
                    st.write(f"{i}. {step}")

        # Display full instructions
        st.subheader("Full Instructions")
        for i, instruction in enumerate(recipe["instructions"], 1):
            st.write(f"{i}. {instruction}")

        # Button and input for alternative suggestion
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("I don't like this recipe, show me another",
                         key=f"dislike_{index}"
                         if index is not None else "dislike"):
                recipe_key = f"show_preference_input_{index}" if index is not None else "show_preference_input"
                st.session_state[recipe_key] = True
                st.rerun()

        # Show preference input if button was clicked
        recipe_key = f"show_preference_input_{index}" if index is not None else "show_preference_input"
        if st.session_state.get(recipe_key, False):
            with col2:
                preference = st.text_input(
                    "What would you prefer instead? (e.g., less spicy, more vegetables, no seafood)",
                    key=f"preference_{index}"
                    if index is not None else "preference")
                if st.button("Generate New Recipe",
                             key=f"generate_{index}"
                             if index is not None else "generate"):
                    # Get the correct preferences based on meal type
                    if "breakfast" in str(index):
                        base_preferences = st.session_state.breakfast_preferences.copy(
                        )
                    else:
                        base_preferences = st.session_state.dinner_preferences.copy(
                        )

                    # Add new preferences from user input
                    base_preferences["additional_preferences"] = [
                        i.strip() for i in preference.split(",") if i.strip()
                    ]

                    new_recipe = get_alternative_recipe(
                        base_preferences, recipe)
                    if new_recipe:
                        if index is not None:
                            if "breakfast" in str(index):
                                st.session_state.breakfast_recipes[int(
                                    index.split('_')[1])] = new_recipe
                            elif "dinner" in str(index):
                                st.session_state.dinner_recipes[int(
                                    index.split('_')[1])] = new_recipe
                            st.session_state[recipe_key] = False
                            st.rerun()
                        else:
                            st.session_state.current_recipe = new_recipe
                            st.session_state[recipe_key] = False
                            st.rerun()

