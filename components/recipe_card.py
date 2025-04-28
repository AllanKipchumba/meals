import streamlit as st
import plotly.express as px

def recipe_card(recipe, show_actions=True):
    """Display a recipe card with all relevant information"""
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(recipe['name'])
            st.write(recipe['description'])
            
            st.write("**Preparation Time:** ", recipe['prep_time'], "minutes")
            st.write("**Servings:** ", recipe['servings'])
            
            # Nutritional information
            nutrition_data = {
                'Nutrient': ['Calories', 'Protein', 'Carbs', 'Fat'],
                'Amount': [
                    recipe['calories'],
                    recipe['protein'],
                    recipe['carbs'],
                    recipe['fat']
                ]
            }
            fig = px.bar(nutrition_data, x='Nutrient', y='Amount',
                        title='Nutritional Information')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if recipe['image_url']:
                st.image(recipe['image_url'], use_column_width=True)
        
        # Ingredients
        st.subheader("Ingredients")
        for ingredient, amount in recipe['ingredients'].items():
            st.write(f"- {amount['amount']} {amount['unit']} {ingredient}")
        
        # Instructions
        st.subheader("Instructions")
        for i, instruction in enumerate(recipe['instructions'], 1):
            st.write(f"{i}. {instruction}")
        
        if show_actions:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Add to Favorites", key=f"fav_{recipe['id']}"):
                    add_to_favorites(recipe['id'])
            
            with col2:
                rating = st.select_slider(
                    "Rate this recipe",
                    options=[1, 2, 3, 4, 5],
                    key=f"rate_{recipe['id']}"
                )
            
            with col3:
                if st.button("Add to Meal Plan", key=f"plan_{recipe['id']}"):
                    add_to_meal_plan(recipe['id'])

def add_to_favorites(recipe_id):
    """Add recipe to user's favorites"""
    if 'user' not in st.session_state:
        st.error("Please log in to add favorites")
        return
    
    db = Database()
    try:
        db.add_favorite(st.session_state['user']['id'], recipe_id)
        st.success("Added to favorites!")
    except Exception as e:
        st.error(f"Failed to add to favorites: {str(e)}")

def add_to_meal_plan(recipe_id):
    """Add recipe to current meal plan"""
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = []
    st.session_state.meal_plan.append(recipe_id)
    st.success("Added to meal plan!")
