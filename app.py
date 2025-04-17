import streamlit as st
from utils.views import (
    display_home,
    display_recipe_generator,
    display_recipe,
    display_subscription_page,
    display_all_recipes,
    display_all_weekend_prep,
    display_favorite_recipes
)
from utils.subscription import init_subscription_plans

def main():
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    
    # Initialize subscription plans
    init_subscription_plans()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Generate Recipe", "Subscription"])
    
    # Display pages based on selection
    if page == "Home":
        display_home()
    elif page == "Generate Recipe":
        display_recipe_generator()
    elif page == "Subscription":
        display_subscription_page()

if __name__ == "__main__":
    main() 