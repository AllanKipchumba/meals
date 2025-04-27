import streamlit as st
# Set page config at the very beginning before any other imports that might use Streamlit
st.set_page_config(
    page_title="Meal Planner",
    initial_sidebar_state="collapsed"
)

from utils.recipe_generator import get_weekly_meal_plan
from utils.shopping_list import generate_shopping_list
from utils.views import display_all_recipes,display_all_weekend_prep,display_recipe,format_recipe_for_printing
from utils.recipe_generator import get_gemini_client
from utils.auth import login_user, handle_callback,check_authentication
from utils.stripe_integration import initialize_stripe, create_checkout_session, verify_checkout_session
from utils.stripe_webhook import handle_webhook
from database.queries import Database
from database.init_db import init_database
import time
import os
import re
import datetime
from dotenv import load_dotenv

# Constants
FREE_MEAL_GEN_LIMIT = 4
PREMIUM_PRICE = 9.99

def get_premium_badge():
    """Returns HTML for a premium badge"""
    return """
    <span style="background-color: #FFD700; color: #000; padding: 2px 6px; 
           border-radius: 4px; font-size: 0.7em; font-weight: bold; margin-left: 5px;">
        PREMIUM
    </span>
    """

def extract_numeric_value(value_str):
    """Extract numeric value from a string that might contain units like 'g', 'mg', etc."""
    if not value_str:
        return 0
    
    # Handle string values
    if isinstance(value_str, str):
        # Remove all non-numeric characters except decimal points
        # This handles cases like '40g', '30 grams', etc.
        numeric_str = re.sub(r'[^\d.]', '', value_str)
        
        if numeric_str:
            try:
                return float(numeric_str)
            except ValueError:
                return 0
    
    # Handle if it's already a number
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return 0

def main():
    # Initialize API key from environment variables (handled by recipe_generator)
    get_gemini_client()
    
    # Load environment variables if not already loaded
    if 'STRIPE_TEST_SECRET_KEY' not in os.environ and os.path.exists('.env'):
        load_dotenv()
    
    # Initialize Stripe (will fail gracefully if keys not available)
    stripe_initialized = initialize_stripe()
    
    # INITIALIZE DATABASE
    init_database()   
    
    if 'auth_checked' not in st.session_state:
        st.session_state['auth_checked'] = False
    
    # Process OAuth callback if present
    if st.query_params.get("state"):
        st.subheader("Authentication Callback")
        st.write("Processing your login...")
        handle_callback()
        return
    
    # Process Stripe checkout callback if present
    session_id = st.query_params.get("session_id")
    if session_id:
        st.subheader("Processing Payment")
        st.write("Verifying your payment...")
        
        success, user_id, transaction_details = verify_checkout_session(session_id)
        
        if success and user_id:
            # Record the payment and set premium status
            db = Database()
            db.record_payment(
                user_id=int(user_id),
                amount=transaction_details['amount'],
                currency=transaction_details['currency'],
                payment_method=transaction_details['payment_method'],
                status='completed',
                transaction_id=transaction_details['transaction_id']
            )
            db.set_premium_status(int(user_id))
            
            # Update session state
            st.session_state['is_premium'] = True
            st.session_state['show_premium_upgrade'] = False
            
            st.success("🎉 Payment successful! You now have premium access with unlimited meal generations.")
            time.sleep(2)  # Give user time to see the message
            # Redirect to main page without query parameters
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Payment verification failed. Please try again.")
            # Add a button to return to the main page
            if st.button("Return to Meal Planner"):
                st.query_params.clear()
                st.rerun()
        
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
    
    if 'auth_checked' not in st.session_state or not st.session_state['auth_checked']:
        with st.spinner(""):            
            is_authenticated = check_authentication()
            st.session_state['auth_checked'] = True
            st.session_state['is_authenticated'] = is_authenticated
            
            # Also set premium status in session state for easy access
            if is_authenticated and 'user' in st.session_state:
                db = Database()
                user_id = st.session_state['user'].get('id')
                is_premium = db.check_premium_status(user_id)
                st.session_state['is_premium'] = is_premium
                st.session_state['meal_gen_count'] = db.get_meal_gen_count(user_id)

    else:
        
        is_authenticated = check_authentication()
        st.session_state['is_authenticated'] = is_authenticated
    
    # Show appropriate content based on authentication status
    if not st.session_state['is_authenticated']:
        login_user()
    else:
        # Check premium status
        db = Database()
        user_id = st.session_state['user'].get('id')
        is_premium = db.check_premium_status(user_id)
        meal_gen_count = db.get_meal_gen_count(user_id)
        
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
            
        # Display premium status at the top
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if is_premium:
                st.success("🌟 Premium Account 🌟")
            else:
                if meal_gen_count >= FREE_MEAL_GEN_LIMIT:
                    st.warning(f"⚠️ You've used all {FREE_MEAL_GEN_LIMIT} meal generations. Upgrade to premium for unlimited generations!")
                    upgrade_col1, upgrade_col2 = st.columns(2)
                    with upgrade_col1:
                        if st.button("💳 Upgrade to Premium ($9.99)", type="primary"):
                            st.session_state.show_premium_upgrade = True
                            st.rerun()
                else:
                    remaining = FREE_MEAL_GEN_LIMIT - meal_gen_count
                    st.info(f"Free plan: {remaining} meal generations remaining")
                    
                    # Show a small upgrade button
                    if st.button("Upgrade to Premium"):
                        st.session_state.show_premium_upgrade = True
                        st.rerun()
        
        # Show premium upgrade screen if requested
        if st.session_state.get('show_premium_upgrade', False):
            st.title("Upgrade to Premium")
            
            # Premium features section
            st.markdown("""
            ### Premium Benefits:
            - **Unlimited** meal plan generations
            - Priority support
            - Advanced customization options
            - Save favorite recipes
            """)
            
            # Pricing section - simplified to show only one option
            st.markdown(f"""
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin: 20px 0; border: 1px solid #ddd;">
                <h3 style="margin-top: 0;">Premium Lifetime Access</h3>
                <h2 style="color: #0066cc;">${PREMIUM_PRICE}</h2>
                <p><strong>One-time payment, lifetime access</strong></p>
                <ul>
                    <li>Unlimited meal generations</li>
                    <li>All premium features</li>
                    <li>No recurring fees</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Simple upgrade button
            if st.button("Upgrade Now", type="primary", key="upgrade_btn"):
                # Check if Stripe is properly initialized
                if not initialize_stripe():
                    st.error("Payment system is not available at this time. Please try again later.")
                else:
                    # Create a Stripe checkout session
                    try:
                        user_id = st.session_state['user'].get('id')
                        
                        # Generate URLs for success and cancel redirects
                        # Use the current URL as the base
                        base_url = "http://localhost:8501"
                        
                        success_url = f"{base_url}"
                        cancel_url = f"{base_url}?cancel=true"
                        
                        # Create the checkout session
                        checkout = create_checkout_session(
                            user_id=user_id,
                            success_url=success_url,
                            cancel_url=cancel_url,
                            price_in_usd=PREMIUM_PRICE
                        )
                        
                        if checkout and 'url' in checkout:
                            # Redirect to Stripe checkout
                            st.markdown(f'<meta http-equiv="refresh" content="0;URL={checkout["url"]}">', unsafe_allow_html=True)
                            st.write("Redirecting to secure payment page...")
                            st.info("If you are not redirected automatically, [click here]({})".format(checkout["url"]))
                        else:
                            st.error("Error creating checkout session. Please try again.")
                    except Exception as e:
                        st.error(f"Error processing upgrade: {str(e)}")
            
            if st.button("← Back to Meal Planner", key="back_btn"):
                st.session_state.show_premium_upgrade = False
                st.rerun()
                
            # Stop here and don't show the meal planner UI
            return

        st.title("Personal Meal Planner")
        st.subheader("Tell us about your preferences")

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
                # Check if user has reached their limit
                if not is_premium and meal_gen_count >= FREE_MEAL_GEN_LIMIT:
                    st.error("You've reached your meal plan generation limit. Please upgrade to premium to continue.")
                    if st.button("Upgrade to Premium", key="upgrade_after_limit"):
                        st.session_state.show_premium_upgrade = True
                        st.rerun()
                    return
                
                # Store the preferences in session state for later use
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
                
               
                if dinner_recipes or breakfast_recipes:
                    # Record this meal generation
                    db.increment_meal_gen_count(user_id)
                    # Re-fetch the current count
                    meal_gen_count = db.get_meal_gen_count(user_id)
                    
                    if not is_premium and meal_gen_count >= FREE_MEAL_GEN_LIMIT:
                        st.warning("This was your last free meal generation. Upgrade to premium for unlimited generations!")
                    
                    st.session_state['dinner_recipes'] = dinner_recipes
                    st.session_state['breakfast_recipes'] = breakfast_recipes
                    st.rerun()

        # Display recipes based on whether it's a weekly plan or single recipe
        if 'dinner_recipes' in st.session_state or 'breakfast_recipes' in st.session_state:
            tabs = st.tabs(["Your Weekly Meal Plan", "Past Recipes"])
            with tabs[0]:
                st.header("Your Weekly Meal Plan")
                
                # Show premium export options for premium users
                if st.session_state.get('is_premium', False):
                    st.markdown("""
                    <div style="background-color: #F0F8FF; padding: 10px; border-radius: 5px; border: 1px solid #ADD8E6;">
                    <h4 style="margin-top: 0;">Premium Features</h4>
                    <ul>
                        <li>Export to PDF</li>
                        <li>Share meal plan via email</li>
                        <li>Save as template</li>
                    </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
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
                    
                    # Add premium feature notes
                    if not st.session_state.get('is_premium', False):
                        st.info("Upgrade to premium to save unlimited favorite recipes!")
                    
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
                        recipe_title = recipe['name']
                        if recipe.get('is_premium_recipe', False):
                            recipe_title += " " + get_premium_badge()
                        
                        with st.expander(
                                f"{recipe_title} (Made on: {recipe['created_at'].strftime('%Y-%m-%d')})"
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
                
                for i, recipe in enumerate(st.session_state['dinner_recipes'], 1):
                    try:
                        db.create_recipe(
                            user_id=st.session_state['user'].get("id"),
                            name=recipe['name'],
                            ingredients=recipe['ingredients'],
                            instructions=recipe['instructions'],
                            calories=extract_numeric_value(recipe['calories']),
                            protein=extract_numeric_value(recipe['macros']['protein']),
                            carbs=extract_numeric_value(recipe['macros']['carbs']),
                            fat=extract_numeric_value(recipe['macros']['total_fat']),
                            tags=recipe.get('tags', []),
                            difficulty=recipe['difficulty'],
                            dietary_info=recipe['dietary_info'],
                            cooking_time=extract_numeric_value(recipe['cooking_time']),
                            prep_time=20,
                            weekend_prep=recipe['weekend_prep'],
                            servings=30,
                        )
                    except Exception as recipe_error:
                        st.error(f"Error saving dinner recipe '{recipe['name']}': {str(recipe_error)}")
                        continue

                for i, recipe in enumerate(st.session_state['breakfast_recipes'], 1):
                    try:
                        db.create_recipe(
                            user_id=st.session_state['user'].get("id"),
                            name=recipe['name'],
                            ingredients=recipe['ingredients'],
                            instructions=recipe['instructions'],
                            calories=extract_numeric_value(recipe['calories']),
                            protein=extract_numeric_value(recipe['macros']['protein']),
                            carbs=extract_numeric_value(recipe['macros']['carbs']),
                            fat=extract_numeric_value(recipe['macros']['total_fat']),
                            tags=recipe.get('tags', []),
                            difficulty=recipe['difficulty'],
                            dietary_info=recipe['dietary_info'],
                            cooking_time=extract_numeric_value(recipe['cooking_time']),
                            prep_time=30,
                            weekend_prep=recipe['weekend_prep'],
                            servings=30,
                        )
                    except Exception as recipe_error:
                        st.error(f"Error saving breakfast recipe '{recipe['name']}': {str(recipe_error)}")
                        continue
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
       

if __name__ == "__main__":
    main()
